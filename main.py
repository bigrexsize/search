import discord
from discord import app_commands
import os
from urllib.parse import urlparse, urlunparse
import requests
import aiofiles
import tempfile
from pathlib import Path

# --- Configuration (Add your volume path) ---
GOOGLE_SEARCH_URL = "https://www.google.com/searchbyimage?image_url="
# Define the temporary directory where files will be saved and cleaned
TEMP_IMAGE_DIR = Path('/images') 
TEMP_IMAGE_DIR.mkdir(exist_ok=True) # Ensure the directory exists

# ... (Intents and Bot Initialization remain the same) ...

@client.event
async def on_message(message):
    # ... (Ignore self-messages) ...
    if message.author == client.user:
        return

    if message.attachments:
        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.startswith('image/'):
                
                # Use Pathlib to create a unique temporary file path within the /images volume
                temp_file_path = TEMP_IMAGE_DIR / f"{message.id}_{attachment.filename}"
                
                try:
                    # 1. DOWNLOAD THE FILE ASYNCHRONOUSLY
                    # Use requests to get the content
                    response = requests.get(attachment.url)
                    response.raise_for_status() # Raise exception for bad status codes
                    
                    # Write the file to the temporary location
                    async with aiofiles.open(temp_file_path, 'wb') as f:
                        await f.write(response.content)
                        
                    # 2. PROCESS THE IMAGE (Use the logic from previous steps)
                    
                    # *** IMPORTANT: Since we downloaded the file, the best search method
                    #    would be to upload it to a stable host (like Imgur) from here.
                    #    However, to maintain the current 'link-only' functionality:
                    
                    # Clean the Discord URL (still needed if you're not using the local file to search)
                    full_url = attachment.url
                    parsed_url = urlparse(full_url)
                    cleaned_url = urlunparse(parsed_url._replace(query='', fragment=''))
                    
                    # Construct the Google search link
                    search_link = f"{GOOGLE_SEARCH_URL}{cleaned_url}"

                    # Send the embed response (omitted for brevity, use the previous embed code)
                    await message.channel.send(f"🔎 Search link generated: {search_link}")
                    
                except requests.exceptions.RequestException as e:
                    await message.channel.send(f"❌ Error downloading image: {e}")
                except Exception as e:
                    await message.channel.send(f"❌ An unexpected error occurred: {e}")
                    
                finally:
                    # 3. CLEANUP: Ensure the temporary file is deleted
                    if temp_file_path.exists():
                        os.remove(temp_file_path)
                        print(f"Cleaned up temporary file: {temp_file_path}")
                        
                return 

# ... (Slash Command and Bot Execution remain the same) ...
