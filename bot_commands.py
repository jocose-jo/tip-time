from discord.ext import commands
from formatting import format_users, format_date
from views import SelectView
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

    @client.command(name='monkey')
    async def print_monkey(ctx):
        with open("./monkey.txt") as monkey_file:
            monkey = ''.join([line for line in monkey_file])
        await ctx.channel.send(f'```{monkey}```')

    @client.command(name='addme')
    async def add_user(ctx):
        if db.save_new_user(ctx.author):
            response = 'added!'
        else:
            response = 'You are already added!'
        await ctx.channel.send(response)

    @client.command(name="strikes?")
    async def fetch_user_strikes(ctx, user: discord.User = None):
        if not user:
            user = ctx.author
        fetched_user = db.find_or_create_user(user)
        message = f"<@{fetched_user['_id']}> has {fetched_user['strikes']} strike(s)"

        await ctx.channel.send(message)

    @client.command(name="strike")
    async def add_strike(ctx, user: discord.User, quantity: int = 1):
        fetched_user = db.find_or_create_user(user)
        updated, new_value = db.update_user_strikes(fetched_user, "plus", quantity)
        message = f"<@{fetched_user['_id']}> now has {new_value} strike(s)"

        await ctx.channel.send(message)

    @client.command(name="unstrike")
    async def remove_strike(ctx, user: discord.User, quantity: int = 1):
        fetched_user = db.find_or_create_user(user)
        updated, new_value = db.update_user_strikes(fetched_user, "subtract", quantity)
        message = f"<@{fetched_user['_id']}> now has {new_value} strike(s)"

        await ctx.channel.send(message)

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

    @client.command(name="start", description="Ask the bot to start around the world")
    async def start_around_the_world(ctx):
        await ctx.channel.send("Start around the world?", view=SelectView())

    @client.command(name="fastest", description="Fastest around the world run, and those who completed it.")
    async def fetch_fastest_rdw_run(ctx):
        query_results = db.fetch_fastest_rdw_runs()
        fastest_rdw_runs = [doc for doc in query_results]
        fastest = fastest_rdw_runs[0]["fastest_run"]
        users = format_users(fastest["users"])
        end_time, total_time = format_date(fastest["end"]), fastest["total_time"].strftime("%H:%M:%S.%f")
        message = f"The fastest Around the World run was completed {end_time} by {users} in {total_time}"
        await ctx.channel.send(f"{message}")
