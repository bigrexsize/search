import os
import discord
from discord.ext import commands

# ✅ Get your Discord token from Railway environment variable
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    raise RuntimeError("❌ Missing environment variable: 'DISCORD_TOKEN' (set it in your Railway project)")

# ✅ Setup Discord bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # needed for text commands

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} — bot is now running!")

@bot.command()
async def ping(ctx):
    """Test if bot is alive"""
    await ctx.send("🏓 Pong!")

# ✅ Example: slash or prefix search command (placeholder for now)
@bot.command()
async def search(ctx, *, query: str):
    await ctx.send(f"🔍 Searching for: {query}\n(You can later make this trigger an image search!)")

# ✅ Start the bot
bot.run(DISCORD_TOKEN)
