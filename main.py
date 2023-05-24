import os
import discord
from dotenv import load_dotenv
from discord.ext import commands

if __name__ == "main":
    load_dotenv()
    TOKEN = os.environ["DISCORD_TOKEN"]

    client = discord.Client()
    bot = commands.Bot(command_prefix='!')

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return
        response = "DALE!"
        await message.channel.send(response)

    @bot.command(name="start")
    async def start_round_da_world(ctx):
        response = "Start round da world !!!"
        await ctx.send(response)

    bot.run(TOKEN)



