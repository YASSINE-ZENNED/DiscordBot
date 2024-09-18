import asyncio
from discord import FFmpegPCMAudio
from discord.errors import ClientException

from utils.utils import getSongConfigs


async def run_song(interaction, ffmpeg_path, song="omg_wow", timeout=30):
    data = await getSongConfigs()
    uri = next((item.get("uri") for item in data if item.get("name") == song), song + ".mp3")
    print(f"Joining voice channel...")
    await interaction.response.send_message("Joining voice channel...")
    channel = interaction.user.voice.channel

    # Check if the bot is already connected to a voice channel
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_connected():
        print("Bot is already connected to a voice channel.")
    else:
        try:
            voice_client = await channel.connect()
            print("Connected to the voice channel.")
        except ClientException as e:
            print(f"Failed to connect to the voice channel: {e}")
            await interaction.channel.send(f"Failed to connect to the voice channel: {e}")
            return

    try:
        print(f"Playing {song}...")
        voice_client.play(
            FFmpegPCMAudio(executable=ffmpeg_path, source="./songs/" + uri)
        )

        # Wait for the song to finish playing or timeout
        await asyncio.wait_for(_wait_for_song_end(voice_client), timeout)
        print("Song finished playing or timeout reached.")

    except asyncio.TimeoutError:
        print("Timeout reached, stopping playback.")
        voice_client.stop()

    except ClientException as e:
        print(f"An error occurred: {e}")
        await interaction.channel.send(f"An error occurred while playing the song: {e}")

    finally:
        await asyncio.sleep(60 * 60)  # 1h delay before disconnecting
        await voice_client.disconnect()
        print("Disconnected from the voice channel.")

async def _wait_for_song_end(voice_client):
    while voice_client.is_playing():
        await asyncio.sleep(0.5)  # Wait a bit before checking again