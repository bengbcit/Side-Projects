import os
import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.lower()

    if content == "!hello":
        await message.channel.send(f"Hello, {message.author.display_name}!")

    elif content == "!ping":
        await message.channel.send("Pong!")

    elif content == "!help":
        await message.channel.send(
            "**Commands:**\n"
            "`!hello` — greet the bot\n"
            "`!ping` — check if the bot is alive\n"
            "`!help` — show this message"
        )


client.run(TOKEN)
