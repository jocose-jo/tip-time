from discord import ComponentType
import discord
import datetime

start_time = datetime.time()
game_one_time = datetime.time()
game_two_time = datetime.time()
game_three_time = datetime.time()
finished = False


class SelectView(discord.ui.View):
    @discord.ui.select(
        select_type=ComponentType.user_select,
        placeholder="Select your partners",
        min_values=2,
        max_values=2,
    )
    async def select_callback(self, select, interaction): # the function called when the user is done selecting options
        await interaction.response.send_message(f"{interaction.user.mention} selects {select.values[0].mention} and {select.values[1].mention} to start AROUND THE WORLD!")
        await interaction.followup.send("Select Game", view=GameView())


class GameView(discord.ui.View):
    @discord.ui.button(label="Start!", row=0, style=discord.ButtonStyle.primary, emoji="✅")
    async def first_button_callback(self, button, interaction):
        start_time = datetime.datetime.now()
        button.disabled = True
        button.label = start_time.strftime("%X")
        await interaction.response.send_message("Around The World has started!")
        await interaction.followup.send(view=self)
        return start_time

    @discord.ui.button(label="Cancel!", row=0, style=discord.ButtonStyle.primary, emoji="❌")
    async def second_button_callback(self, button, interaction):
        button.disabled = True
        button.label = "CANCELED"
        await interaction.response.send_message("Canceled!")
        await interaction.followup.send(view=self)

    @discord.ui.button(label="Game 1", row=1, style=discord.ButtonStyle.primary)
    async def third_button_callback(self, button, interaction):
        button.disabled = True
        game_one_time = datetime.datetime.now()
        button.label = game_one_time.strftime("%X")
        await interaction.response.send_message("Game 1 finished!")
        await interaction.followup.send(view=self)
        return game_three_time

    @discord.ui.button(label="Game 2", row=1, style=discord.ButtonStyle.primary)
    async def fourth_button_callback(self, button, interaction):
        button.disabled = True
        game_two_time = datetime.datetime.now()
        button.label = game_two_time.strftime("%X")
        await interaction.response.send_message("Game 2 finished!")
        await interaction.followup.send(view=self)
        return game_two_time

    @discord.ui.button(label="Game 3", row=1, style=discord.ButtonStyle.primary)
    async def fifth_button_callback(self, button, interaction):
        button.disabled = True
        game_three_time = datetime.datetime.now()
        button.label = game_three_time.strftime("%X")
        finished = True
        # if finished:
        #     final_time = start_time - game_one_time - game_two_time - game_three_time
        #     print(final_time)
        await interaction.response.send_message("Game 3 finished!")
        await interaction.followup.send(view=self)

