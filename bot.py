# bot.py
import os
import io
import asyncio
import aiohttp
from dotenv import load_dotenv

import discord
from discord import app_commands
from discord.ext import commands

# Google Vision API
from google.cloud import vision
from google.api_core.exceptions import GoogleAPIError

# Load .env (optional, helps local testing)
load_dotenv()

# ✅ Your Discord bot token variable
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    raise RuntimeError("❌ Missing environment variable: 'DISCORD_TOKEN' (your Discord bot token)")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Create the Google Vision client (uses GOOGLE_APPLICATION_CREDENTIALS automatically)
vision_client = vision.ImageAnnotatorClient()


async def fetch_image_bytes(url: str) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.read()


def parse_web_detection(response):
    """Simplify the web detection response for Discord display."""
    wd = response.web_detection
    results = {
        "best_guess_labels": [b.label for b in (wd.best_guess_labels or [])],
        "pages_with_matching_images": [],
        "visually_similar_images": [],
    }

    for p in (wd.pages_with_matching_images or []):
        results["pages_with_matching_images"].append({
            "url": p.url,
            "score": getattr(p, "score", None),
        })

    for v in (wd.visually_similar_images or []):
        results["visually_similar_images"].append(v.url)

    return results


@tree.command(name="search", description="Reverse-image search an image (attach or give URL).")
@app_commands.describe(image="Attach an image or paste an image URL (optional).")
async def search_command(interaction: discord.Interaction, image: str = None):
    """Performs reverse image search using Google Vision."""
    await interaction.response.defer()

    img_bytes = None

    # Try to read an attached image if present
    if interaction.message and interaction.message.attachments:
        attachment = interaction.message.attachments[0]
        try:
            img_bytes = await attachment.read()
        except Exception:
            img_bytes = await fetch_image_bytes(attachment.url)
    elif image:
        # Fallback: fetch from given URL
        try:
            img_bytes = await fetch_image_bytes(image)
        except Exception as e:
            await interaction.followup.send(f"⚠️ Failed to fetch image from URL: {e}")
            return
    else:
        await interaction.followup.send("⚠️ Please attach an image or provide an image URL.")
        return

    try:
        g_image = vision.Image(content=img_bytes)
        response = vision_client.web_detection(image=g_image)
    except GoogleAPIError as e:
        await interaction.followup.send(f"❌ Google Vision API error: {e}")
        return
    except Exception as e:
        await interaction.followup.send(f"❌ Unexpected error calling Vision API: {e}")
        return

    if response.error.message:
        await interaction.followup.send(f"❌ Vision API returned error: {response.error.message}")
        return

    parsed = parse_web_detection(response)

    embed = discord.Embed(title="🔍 Image Search Results", color=discord.Color.blue())

    if parsed["best_guess_labels"]:
        embed.add_field(
            name="Best Guess",
            value=", ".join(parsed["best_guess_labels"])[:1024],
            inline=False,
        )

    pages = parsed["pages_with_matching_images"]
    if pages:
        lines = []
        for p in pages[:3]:
            url = p["url"]
            score = p.get("score")
            lines.append(f"[{url}]({url})" + (f" (score {score:.2f})" if score else ""))
        embed.add_field(
            name="Pages with Matching Images (Top 3)",
            value="\n".join(lines)[:1024],
            inline=False,
        )

    sims = parsed["visually_similar_images"]
    if sims:
        embed.set_image(url=sims[0])
        embed.add_field(
            name="Similar Images (sample)",
            value="\n".join(sims[:5])[:1024],
            inline=False,
        )

    if not pages and not sims and not parsed["best_guess_labels"]:
        await interaction.followup.send("⚠️ No useful search results found.")
        return

    await interaction.followup.send(embed=embed)


@bot.event
async def on_ready():
    try:
        await tree.sync()
        print(f"✅ Logged in as {bot.user} — slash commands synced!")
    except Exception as e:
        print("❌ Error syncing commands:", e)


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
