import asyncio
import random
import discord
import os
import platform
import getpass
import fnmatch
import json

from pathlib import Path
from discord.ext import commands
from discord import app_commands, InteractionType
from dotenv import load_dotenv
from utils.run_song import run_song
from utils.send_soundboard_message import send_soundboard_message
from utils.utils import getSongConfigs, saveSongConfigs, help_message

# Load environment variables
dotenv_path = Path("./.env")
load_dotenv(dotenv_path=dotenv_path)
emojis = ["😂", "😄", "😊", "😍", "👍", "😱", "🙌", "💩", "👏", "😜", "🎉", "😁", "💖"]
isDebugModeEnabled = False

ffmpeg_path, channel_id, api_token, guild_id = (
    os.getenv("FFMPEG"),
    int(os.getenv("CHANNEL_ID")),
    os.getenv("API_TOKEN"),
    int(os.getenv("GUILD_ID"))
)

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree
upload_pending = {}

@bot.event
async def on_ready():
    global isDebugModeEnabled
    print(f"Welcome Djaraba gang. {bot.user} is Here. Use me well :D ")

    # Get the channel object using the channel ID
    channel = bot.get_channel(channel_id)
    # Clearing channel
    await clear(channel)
    if channel:
        await channel.send(
            f"Welcome me in Jraba Safi Gang 😍. {bot.user} is Here 😜. Use me well 💖 "
        )

        await help_message(channel)

        # Send a message to the channel
        await send_soundboard_message(channel, ffmpeg_path)

        # Sync commands for each guild the bot is in
        try:
            guild = discord.Object(id=guild_id)
            await tree.sync(guild=guild)
            print(f"Slash commands have been synced with the guild: {guild_id}")
        except Exception as e:
            print(f"An error occurred while syncing commands with the guild: {e}")

        try:
            await tree.sync()
            print("Slash commands have been synced globally.")
        except Exception as e:
            print(f"An error occurred while syncing global commands: {e}")


@bot.event
async def on_message(message):
    global isDebugModeEnabled

    # Don't respond to ourselves
    if message.author == bot.user:
        return

    # Print the message to the console
    print(f"Message from {message.author.name}: {message.content}")

    # React to every message with a like emoji
    random_emoji = random.choice(emojis)
    await message.add_reaction(random_emoji)

    user_id = message.author.id

    if user_id in upload_pending:
        details = upload_pending[user_id]
        name = details["name"]
        emoji = details["emoji"]

        if message.attachments:
            for attachment in message.attachments:
                if attachment.filename.endswith((".mp3", ".wav", ".flac")):
                    filepath = os.path.join("./songs", attachment.filename)
                    if not os.path.isfile(filepath):
                        await attachment.save(filepath)
                        await add_to_json(emoji, name, attachment.filename)
                        await message.channel.send(f"File '{name}' has been uploaded and saved.")
                    else:
                        await message.channel.send(f"File '{attachment.filename}' already exists in the directory.")
                    break
            else:
                await message.channel.send(
                    "Please upload an audio file with one of the following extensions: .mp3, .wav, .flac")

            # Clear the pending upload
            del upload_pending[user_id]
        else:
            await message.channel.send("No file attached. Please try the upload process again.")

    # Process commands after reacting with like emoji
    await bot.process_commands(message)

    counter = 0

    await asyncio.sleep(10)
    async for _ in message.channel.history(limit=None):
        counter += 1

    if counter > 10:
        if message.channel.id == channel_id:
            await clear(message.channel)
            await send_soundboard_message(message.channel, ffmpeg_path)


@bot.event
async def on_interaction(interaction):
    if interaction.type == InteractionType.component:
        if interaction.user.voice is None:
            print("User is not connected to any channel.")
            await interaction.response.send_message(
                "You are not connected to a voice channel!", ephemeral=True
            )
            return
        await run_song(interaction, ffmpeg_path, interaction.data["custom_id"])

@tree.command(name="upload", description="Start the audio file upload process")
@app_commands.describe(name="Name of the song", emoji="Emoji for the song")
async def start_upload(interaction: discord.Interaction, name: str, emoji: str):
    upload_pending[interaction.user.id] = {"name": name, "emoji": emoji}
    await interaction.response.send_message(f"Upload process started for {name}. Please upload the audio file in your next message.", ephemeral=True)

@tree.command(name="delete_song", description="Delete an audio file")
@app_commands.describe(song="Name of the song to delete")
async def delete_file(interaction: discord.Interaction, song: str):
    directory = "./songs/"
    data = await getSongConfigs()
    uri = next((item.get("uri") for item in data if item.get("name") == song), song + ".mp3")
    try:
        file_deleted = False
        for filename in os.listdir(directory):
            if fnmatch.fnmatch(filename, uri):
                filepath = os.path.join(directory, filename)
                os.remove(filepath)
                file_deleted = True
                await interaction.response.send_message(f"File {filename} has been deleted.")
                break

        if not file_deleted:
            await interaction.response.send_message(f"File {uri} not found in the directory.")

        # Remove the song config from the data
        new_data = [item for item in data if item.get("name") != song]
        if len(new_data) == len(data):
            await interaction.response.send_message(f"Song {song} not found in the config file.")
        else:
            with open('data.json', 'w', encoding='utf-8') as file:
                json.dump(new_data, file, ensure_ascii=False, indent=2)
            await interaction.response.send_message(f"Song {song} has been removed from the config file.")

    except Exception as e:
        await interaction.response.send_message(f"An error occurred while deleting the file: {e}")


@tree.command(name="download_song", description="Download a song from the bot")
@app_commands.describe(song="Name of the song to download")
async def download_song(interaction: discord.Interaction, song: str):
    data = await getSongConfigs()
    song_info = next((item for item in data if item["name"] == song), None)

    if song_info is None:
        await interaction.response.send_message(f"The song '{song}' does not exist in the config.", ephemeral=True)
        return

    uri = song_info.get("uri", f"{song}.mp3")
    file_path = os.path.join("./songs", uri)

    if os.path.isfile(file_path):
        await interaction.response.send_message(file=discord.File(file_path), ephemeral=True)
    else:
        await interaction.response.send_message(f"The song file '{uri}' does not exist.", ephemeral=True)


@tree.command(name="toggle_debug_mode", description="Toggle the debug mode")
async def toggle_debug_mode(interaction: discord.Interaction):
    global isDebugModeEnabled
    isDebugModeEnabled = not isDebugModeEnabled
    status = "enabled" if isDebugModeEnabled else "disabled"
    await interaction.response.send_message(f"Debug mode {status}.", ephemeral=True)

@tree.command(name="display_sounds_board", description="Display the sounds board")
async def display_sounds_board(interaction: discord.Interaction):
    await send_soundboard_message(interaction.channel, ffmpeg_path)
    await interaction.response.send_message("Soundboard displayed.", ephemeral=True)

@tree.command(name="where_are_you", description="Get the bot system info (Debug Mode Only)")
async def where_are_you(interaction: discord.Interaction):
    if isDebugModeEnabled:
        await systemInfo(interaction.channel)
        await interaction.response.send_message("System info displayed.", ephemeral=True)
    else:
        await interaction.response.send_message("Debug mode is not enabled.", ephemeral=True)

@tree.command(name="sync", description="Manually sync commands", guild=discord.Object(id=guild_id))
async def sync_commands(interaction: discord.Interaction):
    try:
        guild = discord.Object(id=interaction.guild.id)
        await tree.sync(guild=guild)
        await tree.sync()
        await interaction.response.send_message("Commands have been synced.", ephemeral=True)
        print("Commands have been manually synced.")
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
        print(f"An error occurred while syncing commands: {e}")

async def add_to_json(emoji, name, filename):
    # Load the existing JSON file into a dictionary
    data = await getSongConfigs()

    # Add the emoji and name to the dictionary
    data.append({
        "emoji": emoji,
        "name": name,
        "uri": filename
    })

    # Save the updated dictionary back to the JSON file
    with open("data.json", "w") as file:
        json.dump(data, file)


@commands.has_permissions(manage_messages=True)
async def clear(channel):
    if channel.id == channel_id:
        await channel.purge(limit=None)


async def systemInfo(channel):
    # Get OS information
    os_info = platform.system() + " " + platform.release()
    # Get the current username
    username = getpass.getuser()
    await channel.send(f"I am running in {os_info}. In the name of {username}")
    await send_soundboard_message(channel, ffmpeg_path)


@tree.command(name="die", description="Shut down the bot")
async def die(interaction: discord.Interaction):
    await interaction.response.send_message(f"Bye :pleading_face:")
    exit(0)


bot.run(api_token)
