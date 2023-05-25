from dotenv import load_dotenv
from views import StartView
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


bot = discord.Bot()


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.slash_command(name="start", description="Ask the bot to start around the world")
async def start_around_the_world(ctx):
    await ctx.respond("Start around the world?", view=StartView())


bot.run(TOKEN)

# client.run(TOKEN)
