import discord
from discord import app_commands
import os
from urllib.parse import urlparse, urlunparse

# --- Configuration ---
# The Google reverse image search base URL
GOOGLE_SEARCH_URL = "https://www.google.com/searchbyimage?image_url="

# Intents are required for reading message content and uploads
intents = discord.Intents.default()
# Crucially, enable the message_content intent for reading image uploads
intents.message_content = True

# --- Bot Initialization ---
# Create the Bot instance
client = discord.Client(intents=intents)
# Create a CommandTree to register application (slash) commands
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
    Called every time a message is sent in a channel the bot can see.
    Handles image uploads and generates a reliable Google reverse search link.
    """
    # Ignore messages sent by the bot itself
    if message.author == client.user:
        return

    # Check if the message has an attachment and if it's an image
    if message.attachments:
        for attachment in message.attachments:
            # Simple check for common image file types
            if attachment.content_type and attachment.content_type.startswith('image/'):
                
                # 1. Get the full attachment URL with temporary tokens
                full_url = attachment.url
                
                # 2. Parse the URL and remove the query string (tokens) 🛠️ FIX
                parsed_url = urlparse(full_url)
                # Reconstruct the URL without the query and fragment for a stable link
                cleaned_url = urlunparse(parsed_url._replace(query='', fragment=''))
                
                # 3. Construct the reliable Google search link
                search_link = f"{GOOGLE_SEARCH_URL}{cleaned_url}"

                # --- Use a Discord Embed for a better, clickable look ---
                embed = discord.Embed(
                    title="🔎 Google Reverse Image Search Link",
                    description="Click the **Title Link** above to search Google for this image.",
                    color=discord.Color.blue(), 
                    url=search_link # Makes the title itself clickable
                )
                
                # Show the original image as a thumbnail in the response
                embed.set_thumbnail(url=attachment.url)
                
                embed.add_field(
                    name="Status",
                    value="Link generated using a **stable** version of the image URL.",
                    inline=False
                )

                # Send the response back to the channel
                await message.channel.send(embed=embed)
                
                # Process only the first image attachment and then stop
                return

# --- Slash Command Implementation ---

@tree.command(name="search", description="Provides a link to search an image on Google.")
async def search_command(interaction: discord.Interaction):
    """
    A simple slash command to inform the user how to use the feature.
    """
    await interaction.response.send_message(
        "👋 To search an image, simply **upload an image directly** to this channel.\n"
        "The bot will automatically generate a Google reverse image search link for you!",
        ephemeral=True # Makes the message only visible to the user who ran the command
    )

# --- Bot Execution ---

if __name__ == "__main__":
    # Get the token from the environment variable (e.g., set in Railway or your local environment)
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    
    if not DISCORD_TOKEN:
        print("FATAL: DISCORD_TOKEN environment variable not set.")
        print("Please set the DISCORD_TOKEN to run the bot.")
    else:
        # Run the bot
        client.run(DISCORD_TOKEN)
