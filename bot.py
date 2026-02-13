import discord
import os
from openai import OpenAI

client_ai = OpenAI(api_key=OPENAI_API_KEY)

import trafilatura
import requests
from bs4 import BeautifulSoup


BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

SOURCE_CHANNEL_ID = 1146171312281227265      # replace with your source channel
DESTINATION_CHANNEL_ID = 1471606799969947883 # replace with your c3po channel

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


# -----------------------------
# ARTICLE EXTRACTION (FIXED)
# -----------------------------

def extract_article_text(url):
    try:
        # First attempt: Trafilatura
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded) if downloaded else None

        if text:
            return text

        print("Trafilatura failed, falling back to BeautifulSoup")

        # Second attempt: BeautifulSoup
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        paragraphs = soup.find_all("p")
        fallback = "\n".join(p.get_text(strip=True) for p in paragraphs)

        if fallback.strip():
            return fallback

        print("BeautifulSoup fallback also failed")
        return None

    except Exception as e:
        print("Extraction error:", e)
        return None

# -----------------------------
# OPENAI JOKE GENERATION
# -----------------------------
def send_to_openai(article_text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Write a tight anchor-desk joke with heighten-heighten-undercut rhythm."},
                {"role": "user", "content": article_text}
            ],
            max_tokens=300
        )
        return response["choices"][0]["message"]["content"]

    except Exception as e:
        print("OpenAI error:", e)
        return "Error generating joke."


# -----------------------------
# DISCORD BOT LOGIC
# -----------------------------
@client.event
async def on_message(message):
    # Ignore bot messages
    if message.author.bot:
        return

    # Only react to messages in the source channel
    if message.channel.id != SOURCE_CHANNEL_ID:
        return

    # Only react to links
    if "http" not in message.content:
        return

    article_url = message.content.strip()

    # Extract article text
    article_text = extract_article_text(article_url)

    print("URL:", article_url)
    print("Extracted text:", article_text[:200] if article_text else "NONE")

    if article_text is None:
        await message.channel.send(
            "I couldn’t extract the article text. Want to paste the key details?"
        )
        return

    # Send status to destination channel
    dest_channel = client.get_channel(DESTINATION_CHANNEL_ID)
    if dest_channel is None:
        print("Error: Destination channel not found.")
        return

    await dest_channel.send("Reading article...")

    # Generate jokes
    jokes = send_to_openai(article_text)

    # Send jokes + original link
    await dest_channel.send(f"{jokes}\n\nOriginal article:\n{article_url}")


client.run(BOT_TOKEN)





