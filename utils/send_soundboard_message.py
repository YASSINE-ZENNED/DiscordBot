import discord
from discord.ui import Button, View
from utils.utils import get_songs, getSongConfigs, help_message


async def send_soundboard_message(channel, ffmpeg_path):
    print("Displaying soundboard...")
    songs = get_songs("./songs")
    view = View()
    data = await getSongConfigs()
    added_custom_ids = set()

    for item in data:
        custom_id = item["name"]
        if custom_id in added_custom_ids:
            print(f"Duplicate custom_id detected: {custom_id}. Skipping this button.")
            continue
        added_custom_ids.add(custom_id)

        button = Button(
            label=item["emoji"] + " " + item["name"],
            style=discord.ButtonStyle.primary,
            custom_id=custom_id,
        )
        # This is not needed so far.
        # button.callback = lambda interaction: run_song(interaction, ffmpeg_path, song)
        # Create a view and add the button to it
        view.add_item(button)

    # Send the message with the button
    # Process commands after reacting with like emoji
    await channel.send("\nHave fun", view=view)
    await help_message(channel)