# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**tip-time** is a Discord bot that manages collaborative gaming events and social features. The core feature is "Round the World" (RDW)—a coordinated race where teams play through a series of games sequentially. The bot also tracks user strikes, manages a coin-based betting system, and runs game animations.

## Stack

- **Framework**: py-cord (Discord.py fork) for Discord bot functionality
- **Database**: MongoDB for persistence
- **Language**: Python 3
- **Key Dependencies**: aiohttp, pymongo, python-dotenv, table2ascii

## Architecture

### Core Modules

- **`server.py`**: Entry point. Initializes the Discord bot client and registers all commands.
- **`bot_commands.py`**: All Discord slash commands and message event handlers (strikes, coins, RDW, horse races, bets).
- **`views.py`**: Discord UI components—SelectView (user selection), GameView/GameButton (RDW game tracking), StartView (finish/cancel game buttons), CreateBetModal (bet creation form).
- **`db.py`**: MongoDB interface. Handles users, RDW runs, games, bets, strikes, and coin management. Key collections: Users, RunTimes, RDWGames, Bets.
- **`formatting.py`**: Formatting utilities—time formatting, table generation, user lists.
- **`horse_race.py`**: Horse race game logic and emoji mapping.
- **`env.py`**: Loads environment variables (DISCORD_TOKEN, MONGO_CONNECTION_URL, MODE).

### Data Models

- **User**: Discord ID, name, strikes, coins (initial 500).
- **RDW Run**: users[], status (IN-PROGRESS/COMPLETE/CANCELED), start/end times, game_data[] (each game has name, status, start/end times).
- **RDW Game**: name, lowerName (for case-insensitive queries).
- **Bet**: description, outcomes[], bets[] (outcome, username, amount).

### Command Prefix

Commands use `$` prefix (e.g., `$addme`, `$start`).

## Development Setup

### Initial Setup

```bash
# Create virtual environment
python -m venv env
source env/bin/activate  # or `env\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment file (.env in root)
# Required variables:
# MODE=development (or production)
# DISCORD_TOKEN=<your-bot-token>
# MONGO_CONNECTION_URL=<mongodb-connection-string>
```

### Running the Bot

```bash
python server.py
```

The bot will connect to Discord and listen for commands in the guild where it's registered.

## Key Patterns

- **Guild IDs**: Currently hardcoded as empty list in `server.py`. For faster development with guild-specific commands, populate `guild_ids` (see TODO comment in server.py).
- **Admin checks**: Admin commands check against hardcoded ID list (line 166 in bot_commands.py). Update for your admin users.
- **Async/await**: All command handlers are async; use `await` for Discord operations and db calls.
- **Views persistence**: Discord UI views (buttons, modals) are defined in `views.py` and added to messages via `ctx.channel.send(..., view=ViewClass())`.
- **Error handling**: Currently minimal; commands fail silently on db errors. Consider adding try/except in high-value commands (bets, RDW runs).

## Current Development Context

The `gamba` branch is extending the bot with gambling features (betting and coins). The branch modifies `bot_commands.py` to add/extend betting and coin management.

## Common Tasks

- **Add a new command**: Define an `@client.command()` handler in `bot_commands.py`'s `add_bot_commands()` function.
- **Modify a command**: Edit the handler in `bot_commands.py`. For database changes, update `db.py` accordingly.
- **Add a new Discord UI component**: Create a class in `views.py` (inheriting from `discord.ui.View`, `discord.ui.Button`, etc.) and pass it to `ctx.channel.send()` or `interaction.response.send_message()`.
- **Update leaderboard logic**: Modify the `fetch_fastest_rdw_runs()` query in `db.py` and formatting in `bot_commands.py`'s `fetch_fastest_rdw_run()` handler.
