from discord.ext import commands
from formatting import format_users, format_date_time, convert_to_table
from views import SelectView, CreateBetButton
from horse_race import get_random_unique_horses, trim_name
import discord
import db
import asyncio
import random


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

    @client.check
    async def blacklist(ctx):
        blacklisted = []
        return ctx.author.id not in blacklisted


    @client.command(name='monkey')
    async def print_monkey(ctx):
        with open("assets/monkey.txt") as monkey_file:
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
        default_message = "**Start AROUND THE WORLD**\n\n👤 Solo Run\nTeam: " + ctx.author.name
        await ctx.channel.send(default_message, view=SelectView(ctx.author.id, ctx.guild))

    @client.command(name="leaderboard", description="Fastest around the world runs, and those who completed it.")
    async def fetch_fastest_rdw_run(ctx):
        query_results = db.fetch_fastest_rdw_runs()
        fastest_rdw_runs = [doc for doc in query_results]
        formatted_results = [[idx + 1, format_users(run["users"]), len(run["users"]), format_date_time(run["total_time"]),
                              format_date_time(run["in_game_time"])] for idx, run in enumerate(fastest_rdw_runs)]
        leaderboard_table = convert_to_table(["Rank", "Team", "Size", "Total Time", "In-Game Time"], formatted_results)
        await ctx.channel.send(f'```\n{leaderboard_table}\n```')

    @client.command(name="horserace", description="Start a horse race")
    async def start_horse_race(ctx, *args):
        NAME_LENGTH = 6
        MAX_SCORE = 30

        horses = [f"<a:{horse['name']}:{horse['id']}>" for horse in get_random_unique_horses(ctx.bot.emojis, len(args))]
        names = [trim_name(name, NAME_LENGTH) for name in args]

        # initialize score
        score = [0 for _ in horses]
        # format 'scoreboard'
        horse_race = [f'`{names[i]}|{"="*score[i]}`{horse}`{" "*(MAX_SCORE - score[i])}|`' for i,horse in enumerate(horses)]
        message = await ctx.channel.send('\n'.join(horse_race) + '\n LETS GOOO!')
        await asyncio.sleep(0.5)

        while max(score) < MAX_SCORE:
            # increment random horse
            random_horse = random.randint(0, len(horses) - 1)
            score[random_horse] += 1

            # update 'scoreboard'
            horse_race = [f'`{names[i]}|{"="*score[i]}`{horse}`{" "*(MAX_SCORE - score[i])}|` {"Winner!" if MAX_SCORE == score[i] else ""}' for i, horse in enumerate(horses)]
            await message.edit('\n'.join(horse_race) + '\n LETS GOOO!')

            await asyncio.sleep(0.5)

    @client.command(name="createbet", description="Create a new bet")
    async def create_bet(ctx):
        view = discord.ui.View()
        view.add_item(CreateBetButton())
        await ctx.send("Click the button to create a new bet:", view=view, ephemeral=True)

    @client.command(name="balance", description="Check your coin balance")
    async def check_balance(ctx):
        coins = db.get_user_coins(ctx.author.id)
        await ctx.channel.send(f"<@{ctx.author.id}> has **{coins}** coins")

    @client.command(name="givecoins", description="Admin: give coins to a user")
    async def give_coins(ctx, user: discord.User, amount: int):
        admin_ids = [138756623186264065]
        if ctx.author.id not in admin_ids:
            await ctx.channel.send("You don't have permission to use this command!")
            return

        if amount < 0:
            await ctx.channel.send("Amount must be positive!")
            return

        db.update_user_coins(user.id, amount)
        new_balance = db.get_user_coins(user.id)
        await ctx.channel.send(f"Gave {amount} to <@{user.id}>. New balance: {new_balance}")

    @client.command(name="bets", description="List all open bets")
    async def list_open_bets(ctx):
        open_bets = list(db.fetch_open_bets())
        if not open_bets:
            await ctx.channel.send("No open bets!")
            return

        bets_list = "\n".join([f"{idx+1}. {bet['description']}" for idx, bet in enumerate(open_bets)])
        await ctx.channel.send(f"**Open Bets:**\n{bets_list}")
