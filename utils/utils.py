import os
import json


def get_songs(directory):
    # List all files in the directory (ignore directories)
    filenames_with_extension = [
        f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))
    ]

    # Remove the file extension from each filename
    filenames_without_extension = [
        os.path.splitext(filename)[0] for filename in filenames_with_extension
    ]

    return filenames_without_extension


async def getSongConfigs():
    with open("data.json", "r") as file:
        data = json.load(file)
    return data

async def saveSongConfigs(data):
    with open('data.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

async def help_message(channel):
    await channel.send(
        "To upload new sounds, use the upload command as following: `!upload <name> <emoji> <attachment song>`")
    await channel.send("To delete a sounds, use the delete-song command as following: `!delete-song <name>`")

