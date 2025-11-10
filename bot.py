import os
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

# ✅ Load your Discord token from Railway environment variables
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("❌ Missing environment variable: 'DISCORD_TOKEN' (your Discord bot token)")

# ✅ Set up intents and bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


async def google_image_search(image_bytes):
    """
    Performs an image-based search using Google Lens endpoint.
    This uses the public Lens upload redirect trick (no API key needed).
    """
    async with aiohttp.ClientSession() as session:
        url = "https://lens.google.com/upload"
        form = aiohttp.FormData()
        form.add_field("encoded_image", image_bytes, filename="image.jpg", content_type="image/jpeg")

        async with session.post(url, data=form, allow_redirects=False) as resp:
            if "Location" not in resp.headers:
                return "❌ Google did not return a search URL."
            redirect_url = resp.headers["Location"]
            return f"🔎 **Google Lens Search Result:** {redirect_url}"


@tree.command(name="search", description="Search Google by uploading an image")
async def search(interaction: discord.Interaction, image: discord.Attachment):
    await interaction.response.defer(thinking=True)
    try:
        image_bytes = await image.read()
        result = await google_image_search(image_bytes)
        await interaction.followup.send(result)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}")


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        await tree.sync()
        print("✅ Slash commands synced.")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")


bot.run(TOKEN)
