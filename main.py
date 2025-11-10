import discord
from discord import app_commands
import os
from urllib.parse import urlparse, urlunparse
import requests
import aiofiles
from pathlib import Path

# --- Configuration ---
# The Google reverse image search base URL
GOOGLE_SEARCH_URL = "https://www.google.com/searchbyimage?image_url="

# Define the temporary directory where files will be saved and cleaned (Your Railway Volume)
# This assumes your volume is mounted to the path /images inside the container.
TEMP_IMAGE_DIR = Path('/images') 
TEMP_IMAGE_DIR.mkdir(exist_ok=True) # Ensure the directory exists

# Intents are required for reading message content and uploads
intents = discord.Intents.default()
# Crucially, enable the message_content intent for reading image uploads
intents.message_content = True

# --- Bot Initialization ---
# 1. Create the Bot instance (MUST come before @client.event)
client = discord.Client(intents=intents)
# 2. Create a CommandTree to register application (slash) commands
tree = app_commands.CommandTree(client)

# --- Discord Event Listeners ---

@client.event
async def on_ready():
    """Called when the bot successfully connects to Discord."""
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    # Sync the slash commands with Discord
    try:
        await tree.sync()
        print("Slash commands synced successfully!")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@client.event
async def on_message(message):
    """
    Handles image uploads, downloads the file, generates the search link, and cleans up.
    """
    # Ignore messages sent by the bot itself
    if message.author == client.user:
        return

    # Check if the message has an attachment and if it's an image
    if message.attachments:
        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.startswith('image/'):
                
                # Create a unique temporary file path within the /images volume
                # using the message ID to ensure uniqueness.
                temp_file_path = TEMP_IMAGE_DIR / f"{message.id}_{attachment.filename}"
                
                # --- The Core Download and Cleanup Logic ---
                try:
                    # Inform the user the process has started
                    processing_msg = await message.channel.send("⏳ Detected image upload. Processing file and preparing search link...")

                    # 1. DOWNLOAD THE FILE SYNCHRONOUSLY (requests)
                    response = requests.get(attachment.url, stream=True)
                    response.raise_for_status() # Raise exception for bad status codes
                    
                    # 2. WRITE THE FILE ASYNCHRONOUSLY (aiofiles)
                    # This saves the file to your /images volume.
                    async with aiofiles.open(temp_file_path, 'wb') as f:
                        # Write chunk by chunk to be memory efficient
                        for chunk in response.iter_content(chunk_size=8192):
                            await f.write(chunk)
                        
                    # 3. GENERATE SEARCH LINK (using the unstable Discord URL)
                    # NOTE: This link is still unreliable due to Discord's security, 
                    # but it is the required output.
                    full_url = attachment.url
                    parsed_url = urlparse(full_url)
                    cleaned_url = urlunparse(parsed_url._replace(query='', fragment=''))
                    search_link = f"{GOOGLE_SEARCH_URL}{cleaned_url}"

                    # 4. SEND RESPONSE
                    await processing_msg.delete() # Delete the initial processing message
                    
                    embed = discord.Embed(
                        title="🔎 Google Reverse Image Search Link",
                        description="Click the **Title Link** above to search Google for this image.",
                        color=discord.Color.blue(), 
                        url=search_link
                    )
                    embed.set_thumbnail(url=attachment.url)
                    embed.add_field(
                        name="Note",
                        value=f"Temporary file saved and cleaned up from **{temp_file_path.name}**.",
                        inline=False
                    )

                    await message.channel.send(embed=embed)
                    
                except requests.exceptions.RequestException as e:
                    await message.channel.send(f"❌ Error downloading image from Discord: {e}")
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
                    await message.channel.send(f"❌ An unexpected error occurred during processing.")
                    
                finally:
                    # 5. CLEANUP: Ensure the temporary file is deleted after processing
                    if temp_file_path.exists():
                        os.remove(temp_file_path)
                        print(f"Cleaned up temporary file: {temp_file_path}")
                        
                return

# --- Slash Command Implementation (Remains the same) ---

@tree.command(name="search", description="Provides a link to search an image on Google.")
async def search_command(interaction: discord.Interaction):
    """
    A simple slash command to inform the user how to use the feature.
    """
    await interaction.response.send_message(
        "👋 To search an image, simply **upload an image directly** to this channel.\n"
        "The bot will automatically generate a Google reverse image search link for you!",
        ephemeral=True
    )

# --- Bot Execution (Remains the same) ---

if __name__ == "__main__":
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    
    if not DISCORD_TOKEN:
        print("FATAL: DISCORD_TOKEN environment variable not set.")
    else:
        client.run(DISCORD_TOKEN)
