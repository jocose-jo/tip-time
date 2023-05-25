from discord.ext import commands
import discord
import db


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

        if "dale" in message.content.lower():
            await message.channel.send("DALE!")

        await client.process_commands(message)

    @client.command()
    async def test(ctx, *args):
        print("testing...")
        arguments = ', '.join(args)
        await ctx.channel.send(f'{len(args)} arguments: {arguments}')

    @client.command(name='addme')
    async def add_user(ctx):
        if db.save_new_user(ctx.author):
            response = 'added!'
        else:
            response = 'You are already added!'
        await ctx.channel.send(response)

    @client.command(name="addgame")
    async def add_new_game(ctx, *args):
        game_name = " ".join(args)
        await ctx.channel.send(f'adding new game: {game_name}')
        if db.add_new_rdw_game(game_name):
            response = f'Successfully added new game: {game_name}'
        else:
            response = 'This game already exists :('
        await ctx.channel.send(response)

    @client.command(name="deletegame")
    async def delete_game(ctx, *args):
        game_name = " ".join(args)
        if db.destroy_rdw_game(game_name):
            response = f'Successfully deleted game: {game_name}'
        else:
            response = 'This game doesnt exist :('
        await ctx.channel.send(response)

    @client.command(name="games")
    async def list_rdw_games(ctx):
        rdw_games = db.fetch_rdw_games()
        if rdw_games:
            decorated_rdw_games = "\n".join(rdw_games)
            response = f'Here are all the round the world games:\n\n{decorated_rdw_games}'
        else:
            response = 'There are no Round Da World Games :('
        await ctx.channel.send(response)
