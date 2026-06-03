from discord import ComponentType
from pytz import timezone
import discord
import datetime

import db
from db import fetch_rdw_run_or_create, update_rdw_game
from formatting import format_bet_summary


class SelectView(discord.ui.View):
    @discord.ui.select(
        cls= discord.ui.UserSelect,
        placeholder="Select your partners",
        min_values=2,
        max_values=2,
    )
    async def select_callback(self, select, interaction): # the function called when the user is done selecting options
        await interaction.response.send_message(f"{interaction.user.mention} selects {select.values[0].mention} and {select.values[1].mention} to start AROUND THE WORLD!")
        reduced_users = [{"id": user.id, "name": user.name} for user in select.values]
        reduced_users.append({"id": interaction.user.id, "name": interaction.user.name})
        await interaction.followup.send("Select Game", view=GameView(users=reduced_users))


class GameView(discord.ui.View):
    def __init__(self, run_id=None, users=[]):
        super().__init__(timeout=None)
        self.run_attributes = fetch_rdw_run_or_create(run_id, users, datetime.datetime.now())

        # populate view with buttons fetched from db
        for game in self.run_attributes["game_data"]:
            self.add_item(GameButton(self.run_attributes["_id"], game))


class GameButton(discord.ui.Button):
    def __init__(self, run_id, game):
        super().__init__(label=game["name"], custom_id=f"{game['name']}-{run_id}", style=discord.ButtonStyle.primary, row=0)
        # initialize values to keep track of button state
        self.id = run_id
        self.name = game["name"]
        self.status = game["status"]
        self.start = game["start"]
        self.end = game["end"]
        self.disabled = game["status"] == "COMPLETE" # disable if game is complete

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        if self.status == "PENDING":
            game_attributes = {"_id": self.id, "name": self.name, "status": self.status, "start": datetime.datetime.now(), "end": self.end}
            was_updated, current_status = update_rdw_game(self.id, self.name, "IN-PROGRESS", datetime.datetime.now())
            if was_updated:
                message = f"Current Game: {self.name} - started at: {game_attributes['start'].astimezone(timezone('US/Pacific')).strftime('%I:%M %p')}"
                await interaction.response.send_message(message, view=StartView(game_attributes))
            else:
                await interaction.response.send_message(f"Game is {current_status}")


class StartView(discord.ui.View):
    def __init__(self, attributes):
        super().__init__(timeout=None)
        self.attributes = attributes

    @discord.ui.button(label="Finished!", row=0, style=discord.ButtonStyle.primary, emoji="✅")
    async def finish_button_callback(self, button, interaction):
        button.custom_id = f'finish-{self.attributes["_id"]}'
        end_time = datetime.datetime.now()
        total_time = end_time - self.attributes["start"]
        was_updated, current_status = update_rdw_game(self.attributes["_id"], self.attributes["name"], "COMPLETE", end_time)
        if was_updated:
            await interaction.response.send_message(f"{self.attributes['name']} completed in {total_time}", view=GameView(run_id=self.attributes["_id"]))
            is_run_complete, run_total_time = db.check_if_run_complete(self.attributes["_id"], end_time)
            if is_run_complete:
                await interaction.followup.send(f"AROUND THE WORLD COMPLETED! Total time: {run_total_time}")
        else:
            await interaction.response.send_message(f"Game is {current_status}")

    @discord.ui.button(label="Cancel!", row=0, style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_button_callback(self, button, interaction):
        button.custom_id = f'cancel-{self.attributes["_id"]}'
        button.label = "CANCELED"
        was_updated, current_status = update_rdw_game(self.attributes["_id"], self.attributes["name"], "CANCELED", datetime.datetime.now())
        if was_updated:
            await interaction.response.send_message(f"{self.attributes['name']} has been canceled")
            await interaction.followup.send(view=GameView(run_id=self.attributes["_id"]))
        else:
            await interaction.response.send_message(f"Game is {current_status}")


class CreateBetButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Create Bet", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CreateBetModal())


class CreateBetModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Create a Bet")
        self.add_item(discord.ui.TextInput(label="Bet Description", placeholder="e.g., Who wins the race?"))
        self.add_item(discord.ui.TextInput(label="Outcomes (comma-separated)", placeholder="e.g., Alice,Bob,Carol"))

    async def on_submit(self, interaction: discord.Interaction):
        description = self.children[0].value.strip()
        outcomes_str = self.children[1].value.strip()
        outcomes = [o.strip() for o in outcomes_str.split(",")]

        if len(outcomes) < 2:
            await interaction.response.send_message("You need at least 2 outcomes!", ephemeral=True)
            return

        bet = db.create_bet(interaction.user.id, interaction.channel_id, description, outcomes)
        summary = format_bet_summary(bet)
        await interaction.response.send_message(
            f"**{description}**\n\n{summary}",
            view=BetView(bet, interaction.user.id)
        )
        message = await interaction.original_response()
        db.update_bet_message_id(str(bet["_id"]), message.id)


class BetView(discord.ui.View):
    def __init__(self, bet, creator_id):
        super().__init__(timeout=None)
        self.bet = bet
        self.creator_id = creator_id

        for outcome in bet["outcomes"]:
            self.add_item(OutcomeButton(str(bet["_id"]), outcome, bet["status"]))

        self.add_item(ResolveButton(str(bet["_id"]), creator_id, bet["status"]))


class OutcomeButton(discord.ui.Button):
    def __init__(self, bet_id, outcome, bet_status):
        super().__init__(label=outcome, custom_id=f"bet-{bet_id}-{outcome}", style=discord.ButtonStyle.primary)
        self.bet_id = bet_id
        self.outcome = outcome
        self.disabled = bet_status != "OPEN"

    async def callback(self, interaction: discord.Interaction):
        bet = db.fetch_bet(self.bet_id)
        if bet["status"] != "OPEN":
            await interaction.response.send_message("This bet is already settled!", ephemeral=True)
            return

        user_coins = db.get_user_coins(interaction.user.id)
        await interaction.response.send_modal(WagerModal(self.bet_id, self.outcome, user_coins, interaction.user.id, interaction.user.name, interaction.message))


class WagerModal(discord.ui.Modal):
    def __init__(self, bet_id, outcome, user_coins, user_id, username, message):
        super().__init__(title=f"Bet on {outcome}")
        self.bet_id = bet_id
        self.outcome = outcome
        self.user_coins = user_coins
        self.user_id = user_id
        self.username = username
        self.message = message
        self.add_item(discord.ui.TextInput(label=f"Amount (max {user_coins})", placeholder="100"))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.children[0].value.strip())
        except ValueError:
            await interaction.response.send_message("Please enter a valid number!", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("Bet amount must be positive!", ephemeral=True)
            return

        if amount > self.user_coins:
            await interaction.response.send_message(f"You only have {self.user_coins} coins!", ephemeral=True)
            return

        db.add_wager_to_bet(self.bet_id, self.user_id, self.username, self.outcome, amount)
        db.update_user_coins(self.user_id, -amount)

        bet = db.fetch_bet(self.bet_id)
        summary = format_bet_summary(bet)
        await self.message.edit(content=f"**{bet['description']}**\n\n{summary}", view=BetView(bet, bet["creator_id"]))
        await interaction.response.send_message(f"You bet {amount} coins on {self.outcome}!", ephemeral=True)


class ResolveButton(discord.ui.Button):
    def __init__(self, bet_id, creator_id, bet_status):
        super().__init__(label="Resolve", custom_id=f"resolve-{bet_id}", style=discord.ButtonStyle.success)
        self.bet_id = bet_id
        self.creator_id = creator_id
        self.disabled = bet_status != "OPEN"

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.creator_id:
            await interaction.response.send_message("Only the bet creator can resolve!", ephemeral=True)
            return

        bet = db.fetch_bet(self.bet_id)
        if bet["status"] != "OPEN":
            await interaction.response.send_message("This bet is already settled!", ephemeral=True)
            return

        await interaction.response.send_modal(ResolveModal(self.bet_id, bet["outcomes"], interaction.message))


class ResolveModal(discord.ui.Modal):
    def __init__(self, bet_id, outcomes, message):
        super().__init__(title="Select Winner")
        self.bet_id = bet_id
        self.outcomes = outcomes
        self.message = message
        self.add_item(discord.ui.TextInput(label="Winning outcome", placeholder=", ".join(outcomes)))

    async def on_submit(self, interaction: discord.Interaction):
        winner = self.children[0].value.strip()
        if winner not in self.outcomes:
            await interaction.response.send_message(f"Invalid outcome! Choose from: {', '.join(self.outcomes)}", ephemeral=True)
            return

        settled_bet = db.settle_bet(self.bet_id, winner)

        total_pot = sum(w["amount"] for w in settled_bet["bets"])
        winning_wagers = [w for w in settled_bet["bets"] if w["outcome"] == winner]
        total_on_winner = sum(w["amount"] for w in winning_wagers)

        payouts = []
        for wager in winning_wagers:
            payout = int((wager["amount"] / total_on_winner) * total_pot) if total_on_winner > 0 else 0
            db.update_user_coins(wager["user_id"], payout)
            payouts.append((wager["username"], wager["amount"], payout))

        results = f"**Bet settled: {settled_bet['description']}**\n\nWinner: **{winner}**\n\n"
        if payouts:
            results += "**Payouts:**\n"
            for username, bet_amount, payout in payouts:
                results += f"  {username}: bet {bet_amount} → won {payout} coins\n"

        losing_wagers = [w for w in settled_bet["bets"] if w["outcome"] != winner]
        if losing_wagers:
            results += "\n**Losses:**\n"
            for wager in losing_wagers:
                results += f"  {wager['username']}: bet {wager['amount']} on {wager['outcome']} → lost\n"

        await self.message.edit(content=results, view=discord.ui.View())
        await interaction.response.send_message("Bet resolved!", ephemeral=True)
