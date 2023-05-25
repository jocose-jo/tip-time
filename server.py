from env import DISCORD_TOKEN, MODE

import bot_commands

"""
Tip-time discord bot. Powered by Pycord
"""

if __name__ == "__main__":
    guild_ids = []
    if MODE == 'development':
        # TODO: get this to load in guild_ids to register new commands for faster development
        pass
    client = bot_commands.init_client()
    bot_commands.add_bot_commands(client)

    client.run(DISCORD_TOKEN)
