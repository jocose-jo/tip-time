from discord.ext import commands
import discord
from db import save_new_user


def init_client(prefix='$'):
    return commands.Bot(command_prefix=prefix, intents=discord.Intents.all())


def add_bot_commands(client):
    @client.event
    async def on_ready():
        print(f'We have logged in as {client.user}')

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        response = "DALE!"
        await message.channel.send(response)
        await client.process_commands(message)

    @client.command()
    async def test(ctx, *args):
        print("testing...")
        arguments = ', '.join(args)
        await ctx.channel.send(f'{len(args)} arguments: {arguments}')

    @client.command(name='addme')
    async def add_user(ctx: discord.ApplicationContext):
        save_new_user(ctx.author)
        await ctx.channel.send('Saved to DB')

