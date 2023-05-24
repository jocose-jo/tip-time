from dotenv import load_dotenv
import discord
import os

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
load_dotenv()
TOKEN = os.environ["DISCORD_TOKEN"]


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    response = "DALE!"
    await message.channel.send(response)

client.run(TOKEN)
