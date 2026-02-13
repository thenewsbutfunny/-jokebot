import os
import discord
import requests
from newspaper import Article


BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- CONFIG ---

SOURCE_CHANNEL_ID = 1146171312281227265      # where article links appear
DESTINATION_CHANNEL_ID = 1471606799969947883  # where jokes should be posted

# ---------------

def extract_article_text(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        text = f"{article.title}\n\n{article.text}"
        return text[:5000]  # keep it safe for the model
    except Exception as e:
        return f"Could not extract article text: {e}"

# ----

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

def send_to_openai(article_text):
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [
               {"role": "system", "content": """
You write Weekend Update–style jokes in Matthew’s exact comedic voice.

STRUCTURE (follow this every time):

1. CLEAN FACTUAL SETUP
   - One sentence.
   - Straight news copy.
   - No jokes, no commentary, no editorializing.

2. HEIGHTEN
   - Add a second factual detail that escalates the situation.
   - Still no jokes.

3. HEIGHTEN AGAIN
   - Add a third factual detail that pushes the absurdity further.
   - Still no jokes.

4. UNDERCUT PUNCHLINE
   - One sentence.
   - Dry, simple, understated.
   - Trust the audience to connect the dots.
   - No explaining the joke.
   - No clever wordplay unless extremely minimal.
   - Delivery should feel like Kevin Nealon’s formality with Norm Macdonald’s deadpan undercut.

STYLE RULES:
- The punchline must ONLY use information already stated in the setups.
- Do NOT introduce new facts, characters, foods, locations, or concepts.
- Prefer contrast over cleverness.
- Never overwrite the punchline.
- Never explain why something is funny.
- Keep the entire packet tight and economical.
- Leave room for performance choices (tone shifts, deadpan tags, graphics, accents).
- No hyperlinks in the final joke.

TIGHTENING MODE:
If asked to “tighten,” “sharpen,” or “punch up” a joke, rewrite it:
- shorter,
- drier,
- with a cleaner undercut,
- and with zero added information.
"""},
                {
                    "role": "user",
                    "content": f"Here is an article. Extract the core news event and write one joke packet in the style described above:\n\n{article_text}"
                }
            ]
        }
    )
    return response.json()["choices"][0]["message"]["content"]

@client.event
async def on_message(message):
    # Only react to messages in the source channel
    if message.channel.id != SOURCE_CHANNEL_ID:
        return

    if message.author.bot:
        return

    # Only react to links
    if "http" in message.content:
        dest_channel = client.get_channel(DESTINATION_CHANNEL_ID)

        if dest_channel is None:
            print("Error: Destination channel not found.")
            return

        await dest_channel.send("Reading article…")

        article_url = message.content.strip()
        article_text = extract_article_text(article_url)

        jokes = send_to_openai(article_text)

        await dest_channel.send(jokes)

client.run(BOT_TOKEN)