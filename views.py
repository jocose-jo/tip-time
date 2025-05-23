from discord import ComponentType
from pytz import timezone
import discord
import datetime

import db
from db import fetch_rdw_run_or_create, update_rdw_game


class SelectView(discord.ui.View):
    @discord.ui.select(
        select_type=ComponentType.user_select,
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
