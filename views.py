from discord import ComponentType
from pytz import timezone
import discord
import datetime

import db
from db import fetch_rdw_run_or_create, update_rdw_game, fetch_rdw_run
from formatting import format_bet_summary, format_duration, calculate_rdw_reward, format_team_mentions, format_team_summary, format_run_team


class TeammateSelect(discord.ui.Select):
    def __init__(self, initiator_id, guild):
        self.initiator_id = initiator_id
        self.guild = guild
        self.selected_users_map = {}

        options = [discord.SelectOption(label="Solo", value="solo", emoji="😈")]
        MAX_OPTIONS = 25  # Discord Select limit

        for member in guild.members:
            if len(options) >= MAX_OPTIONS:
                break
            if member.id != initiator_id:
                display_name = member.display_name or member.name
                emoji = "🤖" if member.bot else "👤"
                label = f"{display_name}"
                options.append(discord.SelectOption(label=label, value=str(member.id), emoji=emoji))
                self.selected_users_map[str(member.id)] = member

        super().__init__(
            placeholder="Select your teammates (0-2 partners)",
            min_values=0,
            max_values=2,
            options=options if options else [discord.SelectOption(label="No other users available", value="none", disabled=True)]
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values and self.values[0] not in ("none", "solo"):
            self.view.selected_users = [self.selected_users_map[user_id] for user_id in self.values]
        else:
            self.view.selected_users = []

        await interaction.response.defer()
        await self.view.update_team_display(interaction.message, interaction.user.name, self.view.selected_users)


class SelectView(discord.ui.View):
    def __init__(self, initiator_id, guild):
        super().__init__(timeout=None)
        self.selected_users = []
        self.initiator_id = initiator_id
        self.guild = guild
        self.add_item(TeammateSelect(initiator_id, guild))

    async def update_team_display(self, message, initiator_name, selected_users):
        run_type, team_display = format_team_summary(selected_users, initiator_name)
        content = f"**Start AROUND THE WORLD**\n\n{run_type}\n{team_display}"
        await message.edit(content=content, view=self)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, row=1)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.selected_users) > 2:
            await interaction.response.send_message("You can select a maximum of 2 partners!", ephemeral=True)
            return

        reduced_users = [{"id": user.id, "name": user.name} for user in self.selected_users]
        reduced_users.append({"id": interaction.user.id, "name": interaction.user.name})

        selected_mentions = [user.mention for user in self.selected_users]
        team_mention = format_team_mentions(interaction.user.mention, selected_mentions)

        await interaction.channel.send(f"{team_mention} start(s) AROUND THE WORLD!")
        await interaction.channel.send("Select Game", view=GameView(users=reduced_users))
        await interaction.message.delete()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, row=1)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Selection canceled.", ephemeral=True)
        await interaction.message.delete()


class GameView(discord.ui.View):
    def __init__(self, run_id=None, users=[], run_attributes=None):
        super().__init__(timeout=None)
        if run_attributes:
            self.run_attributes = run_attributes
        else:
            self.run_attributes = fetch_rdw_run_or_create(run_id, users, datetime.datetime.now())

        # populate view with buttons fetched from db
        for i, game in enumerate(self.run_attributes["game_data"]):
            runs_id = self.run_attributes["_id"]
            button_id = runs_id + i
            row = i // 5
            self.add_item(GameButton(button_id, runs_id, game, row, self.run_attributes))


class GameButton(discord.ui.Button):
    def __init__(self, button_id, run_id, game, row=0, run_attributes=None):
        super().__init__(label=game["name"], custom_id=f"{game['name']}-{button_id}", style=discord.ButtonStyle.primary, row=row)
        # initialize values to keep track of button state
        self.id = button_id
        self.run_id = run_id
        self.name = game["name"]
        self.status = game["status"]
        self.start = game["start"]
        self.end = game["end"]
        self.disabled = game["status"] == "COMPLETE" # disable if game is complete
        self.run_attributes = run_attributes

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        run = self.run_attributes or fetch_rdw_run(self.run_id)
        user_ids = [user["id"] for user in run["users"]]
        if interaction.user.id not in user_ids:
            await interaction.response.send_message("Only runners can start games!", ephemeral=True)
            return

        if self.status == "PENDING":
            game_start_time = datetime.datetime.now()
            team_info = format_run_team(run["users"])
            game_attributes = {"_id": self.run_id, "name": self.name, "status": self.status, "start": game_start_time, "end": self.end}
            was_updated, current_status = update_rdw_game(self.run_id, self.name, "IN-PROGRESS", game_start_time)
            if was_updated:
                message = f"**Current Game: {self.name}**\n{team_info}\nStarted at: {game_start_time.astimezone(timezone('US/Pacific')).strftime('%I:%M %p')}"
                await interaction.channel.send(message, view=StartView(game_attributes, run))
                await interaction.message.delete()
            else:
                await interaction.response.send_message(f"Game is {current_status}")


class StartView(discord.ui.View):
    def __init__(self, attributes, run=None):
        super().__init__(timeout=None)
        self.attributes = attributes
        self.run = run

    @discord.ui.button(label="Finished!", row=0, style=discord.ButtonStyle.primary, emoji="✅")
    async def finish_button_callback(self, interaction: discord.Interaction, button):
        # button.custom_id = f'finish-{self.attributes["_id"]}'
        run = self.run or fetch_rdw_run(self.attributes["_id"])
        user_ids = [user["id"] for user in run["users"]]
        if interaction.user.id not in user_ids:
            await interaction.response.send_message("Only runners can finish games!", ephemeral=True)
            return

        end_time = datetime.datetime.now()
        total_time = end_time - self.attributes["start"]
        team_info = format_run_team(run["users"])
        was_updated, current_status = update_rdw_game(self.attributes["_id"], self.attributes["name"], "COMPLETE", end_time)
        if was_updated:
            updated_run = fetch_rdw_run(self.attributes["_id"])
            splits_content = f"\n\n**Game Splits:**\n"
            for game in updated_run["game_data"]:
                if game["status"] == "COMPLETE":
                    game_time = game["end"] - game["start"]
                    splits_content += f"• {game['name']}: {format_duration(game_time)}\n"
            game_view_message = await interaction.channel.send(f"{team_info}\n**{self.attributes['name']}** completed in {format_duration(total_time)}{splits_content}", view=GameView(run_id=self.attributes["_id"], run_attributes=updated_run))
            await interaction.message.delete()
            is_run_complete, run_total_time = db.check_if_run_complete(self.attributes["_id"], end_time)
            if is_run_complete:
                run = fetch_rdw_run(self.attributes["_id"])
                db.award_rdw_completion_coins(self.attributes["_id"])
                reward = calculate_rdw_reward(run["end"] - run["start"])

                splits_message = f"{team_info} has completed AROUND THE WORLD!\nTotal time: {format_duration(run_total_time)}\n\n**Game Splits:**\n"
                for game in run["game_data"]:
                    if game["status"] == "COMPLETE":
                        game_time = game["end"] - game["start"]
                        splits_message += f"• {game['name']}: {format_duration(game_time)}\n"
                splits_message += f"\n🎉 Each participant earned **{reward}** coins!"
                await interaction.channel.send(splits_message)
                await game_view_message.delete()
        else:
            await interaction.response.send_message(f"Game is {current_status}")

    @discord.ui.button(label="Cancel!", row=0, style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_button_callback(self, interaction: discord.Interaction, button):
        # button.custom_id = f'cancel-{self.attributes["_id"]}'
        run = self.run or fetch_rdw_run(self.attributes["_id"])
        user_ids = [user["id"] for user in run["users"]]
        if interaction.user.id not in user_ids:
            await interaction.response.send_message("Only runners can cancel games!", ephemeral=True)
            return

        button.label = "CANCELED"
        was_updated, current_status = update_rdw_game(self.attributes["_id"], self.attributes["name"], "CANCELED", datetime.datetime.now())
        if was_updated:
            updated_run = fetch_rdw_run(self.attributes["_id"])
            team_info = format_run_team(updated_run["users"])
            splits_content = f"\n\n**Game Splits:**\n"
            for game in updated_run["game_data"]:
                if game["status"] == "COMPLETE":
                    game_time = game["end"] - game["start"]
                    splits_content += f"• {game['name']}: {format_duration(game_time)}\n"
            await interaction.response.send_message(f"{self.attributes['name']} has been canceled", ephemeral=True)
            await interaction.channel.send(f"{team_info}{splits_content}", view=GameView(run_id=self.attributes["_id"], run_attributes=updated_run))
            await interaction.message.delete()
        else:
            await interaction.response.send_message(f"Game is {current_status}")


class CreateBetButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Create Bet", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CreateBetModal(interaction.message))


class CreateBetModal(discord.ui.Modal):
    def __init__(self, button_message=None):
        super().__init__(title="Create a Bet")
        self.button_message = button_message
        self.add_item(discord.ui.TextInput(label="Bet Description", placeholder="e.g., Who wins the race?"))
        self.add_item(discord.ui.TextInput(label="Outcomes (comma-separated)", placeholder="e.g., Alice,Bob,Carol"))

    async def on_submit(self, interaction: discord.Interaction):
        description = self.children[0].value.strip()
        outcomes_str = self.children[1].value.strip()
        outcomes = [o.strip() for o in outcomes_str.split(",")]

        if len(outcomes) < 2:
            await interaction.response.send_message("You need at least 2 outcomes!", ephemeral=True)
            return

        creator_name = interaction.user.display_name or interaction.user.name
        db.find_or_create_user(interaction.user, creator_name)
        bet = db.create_bet(interaction.user.id, creator_name, interaction.channel_id, description, outcomes)
        summary = format_bet_summary(bet)
        await interaction.response.send_message(
            f"**{description}**\n\n{summary}",
            view=BetView(bet, interaction.user.id)
        )
        message = await interaction.original_response()
        db.update_bet_message_id(str(bet["_id"]), message.id)

        if self.button_message:
            try:
                await self.button_message.delete()
            except discord.NotFound:
                pass


class BetView(discord.ui.View):
    def __init__(self, bet, creator_id):
        super().__init__(timeout=None)
        self.bet = bet
        self.creator_id = creator_id

        for outcome in bet["outcomes"]:
            self.add_item(OutcomeButton(str(bet["_id"]), outcome, bet["status"]))

        self.add_item(CloseButton(str(bet["_id"]), creator_id, bet["status"]))
        self.add_item(ResolveButton(str(bet["_id"]), creator_id, bet["status"]))


class OutcomeButton(discord.ui.Button):
    def __init__(self, bet_id, outcome, bet_status):
        super().__init__(label=outcome, custom_id=f"bet-{bet_id}-{outcome}", style=discord.ButtonStyle.primary)
        self.bet_id = bet_id
        self.outcome = outcome
        self.disabled = bet_status != "OPEN"

    async def callback(self, interaction: discord.Interaction):
        bet = db.fetch_bet(self.bet_id)
        if bet["status"] == "CLOSED":
            await interaction.response.send_message("No longer receiving new bets!", ephemeral=True)
            return
        if bet["status"] != "OPEN":
            await interaction.response.send_message("This bet is already settled!", ephemeral=True)
            return

        existing_outcome = db.user_has_bet(self.bet_id, interaction.user.id)
        if existing_outcome:
            await interaction.response.send_message(f"You've already bet on {existing_outcome}!", ephemeral=True)
            return

        username = interaction.user.display_name or interaction.user.name
        user_coins = db.get_user_coins(interaction.user.id)
        db.find_or_create_user(interaction.user, username)
        await interaction.response.send_modal(WagerModal(self.bet_id, self.outcome, user_coins, interaction.user.id, username, interaction.message))


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
        existing_outcome = db.user_has_bet(self.bet_id, self.user_id)
        if existing_outcome:
            await interaction.response.send_message(f"You've already bet on {existing_outcome}!", ephemeral=True)
            return

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


class CloseButton(discord.ui.Button):
    def __init__(self, bet_id, creator_id, bet_status):
        super().__init__(label="Close Bets", custom_id=f"close-{bet_id}", style=discord.ButtonStyle.danger)
        self.bet_id = bet_id
        self.creator_id = creator_id
        self.disabled = bet_status != "OPEN"

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.creator_id:
            await interaction.response.send_message("Only the bet creator can close the bet!", ephemeral=True)
            return

        bet = db.fetch_bet(self.bet_id)
        if bet["status"] != "OPEN":
            await interaction.response.send_message("This bet is already closed or settled!", ephemeral=True)
            return

        db.close_bet(self.bet_id)
        bet = db.fetch_bet(self.bet_id)
        summary = format_bet_summary(bet)
        await interaction.message.edit(content=f"**{bet['description']}**\n\n{summary}\n\n⛔ **No longer receiving new bets**", view=BetView(bet, self.creator_id))


class ResolveButton(discord.ui.Button):
    def __init__(self, bet_id, creator_id, bet_status):
        super().__init__(label="Resolve", custom_id=f"resolve-{bet_id}", style=discord.ButtonStyle.success)
        self.bet_id = bet_id
        self.creator_id = creator_id
        self.disabled = bet_status == "SETTLED"

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.creator_id:
            await interaction.response.send_message("Only the bet creator can resolve!", ephemeral=True)
            return

        bet = db.fetch_bet(self.bet_id)
        if bet["status"] == "SETTLED":
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
