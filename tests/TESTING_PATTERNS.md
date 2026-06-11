# Testing Patterns Guide

Quick reference for common testing patterns in tip-time.

## Testing Discord Commands

Commands in `bot_commands.py` use Discord contexts. Mock them like this:

### Basic Command Test

```python
import pytest
from unittest.mock import patch, MagicMock
from bot_commands import my_command

@pytest.mark.asyncio
async def test_my_command(self, mock_ctx):
    # Set up the context
    mock_ctx.author.id = 123456789
    mock_ctx.author.name = "TestUser"
    
    # Mock any database calls
    with patch('bot_commands.fetch_user') as mock_fetch:
        mock_fetch.return_value = {"_id": 123456789, "name": "TestUser", "coins": 500}
        
        # Call your command
        await my_command(mock_ctx)
        
        # Verify the response
        mock_ctx.send.assert_called_once()
        call_args = mock_ctx.send.call_args[0][0]
        assert "expected text" in call_args
```

### Test with Database Changes

```python
@pytest.mark.asyncio
async def test_command_updates_database(self, mock_ctx, mock_users_collection):
    with patch('bot_commands.user_collection', mock_users_collection):
        # Insert initial data
        mock_users_collection.insert_one({"_id": 123, "name": "User", "coins": 100})
        
        # Run command
        await my_command(mock_ctx)
        
        # Verify database was updated
        user = mock_users_collection.find_one({"_id": 123})
        assert user["coins"] == 150  # or whatever changed
```

## Testing Discord Interactions (Slash Commands)

For slash commands using `interaction.response`:

```python
@pytest.mark.asyncio
async def test_slash_command(self, mock_interaction):
    # Set up the interaction
    mock_interaction.user.id = 987654321
    
    # Mock any db calls
    with patch('bot_commands.fetch_user') as mock_fetch:
        mock_fetch.return_value = {"_id": 987654321, "coins": 500}
        
        # Call your command
        await my_slash_command(mock_interaction)
        
        # Verify response was sent
        mock_interaction.response.send_message.assert_called_once()
```

## Testing Views (Buttons, Select Menus)

For Discord UI components:

```python
@pytest.mark.asyncio
async def test_button_callback(self, mock_interaction):
    button = GameButton(
        button_id=100,
        run_id=1234567890,
        game={"name": "Game", "status": "PENDING", "start": None, "end": None}
    )
    
    # Set button's view (required for callback)
    button.view = MagicMock()
    button.view.run_attributes = {"_id": 1234567890, "game_data": [...]}
    
    # Call the callback
    await button.callback(mock_interaction)
    
    # Verify response
    mock_interaction.response.defer.assert_called_once()
```

## Testing Database Operations

### User Operations

```python
def test_user_flow(self, mock_users_collection):
    # Create
    mock_users_collection.insert_one({
        "_id": 111,
        "name": "Alice",
        "coins": 500,
        "strikes": 0
    })
    
    # Read
    user = mock_users_collection.find_one({"_id": 111})
    assert user["name"] == "Alice"
    
    # Update
    mock_users_collection.update_one({"_id": 111}, {'$set': {'coins': 600}})
    
    # Verify
    user = mock_users_collection.find_one({"_id": 111})
    assert user["coins"] == 600
    
    # Delete
    mock_users_collection.delete_one({"_id": 111})
    assert mock_users_collection.find_one({"_id": 111}) is None
```

### RDW Run Operations

```python
def test_rdw_run_flow(self, mock_run_times_collection):
    # Create run
    run_id = 1234567890
    run = {
        "_id": run_id,
        "users": ["Alice", "Bob"],
        "status": "IN-PROGRESS",
        "start": datetime.now(),
        "game_data": [
            {"name": "Game1", "status": "PENDING", "start": None, "end": None},
            {"name": "Game2", "status": "PENDING", "start": None, "end": None},
        ]
    }
    mock_run_times_collection.insert_one(run)
    
    # Update game status
    mock_run_times_collection.update_one(
        {"_id": run_id, "game_data.name": "Game1"},
        {'$set': {
            "game_data.$.start": datetime.now(),
            "game_data.$.status": "IN-PROGRESS"
        }}
    )
    
    # Verify
    result = mock_run_times_collection.find_one({"_id": run_id})
    game1 = next(g for g in result["game_data"] if g["name"] == "Game1")
    assert game1["status"] == "IN-PROGRESS"
```

### Bet Operations

```python
def test_bet_workflow(self, mock_bets_collection):
    # Create bet
    bet = {
        "creator_id": 111,
        "description": "Will team A win?",
        "outcomes": ["Yes", "No"],
        "status": "OPEN",
        "bets": [],
        "winner_outcome": None,
    }
    result = mock_bets_collection.insert_one(bet)
    bet_id = result.inserted_id
    
    # Add wager
    mock_bets_collection.update_one(
        {"_id": bet_id},
        {'$push': {'bets': {
            "user_id": 222,
            "username": "Alice",
            "outcome": "Yes",
            "amount": 100
        }}}
    )
    
    # Settle
    mock_bets_collection.update_one(
        {"_id": bet_id},
        {'$set': {'status': 'SETTLED', 'winner_outcome': 'Yes'}}
    )
    
    # Verify
    settled_bet = mock_bets_collection.find_one({"_id": bet_id})
    assert settled_bet["status"] == "SETTLED"
    assert len(settled_bet["bets"]) == 1
```

## Mocking External Dependencies

### Patching Database Imports

```python
from unittest.mock import patch

@pytest.mark.asyncio
async def test_with_patched_db(self, mock_users_collection):
    with patch('bot_commands.user_collection', mock_users_collection):
        # Your command here will use the mocked collection
        await my_command(mock_ctx)
```

### Mocking Discord API Calls

```python
def test_with_mocked_discord_api(self, mock_ctx):
    # Mock getting a user from Discord API
    mock_ctx.guild.get_member = MagicMock(return_value=MockMember())
    
    # Mock fetching from Discord
    mock_user = MagicMock()
    mock_user.name = "DiscordUser"
    mock_ctx.bot.get_user = MagicMock(return_value=mock_user)
```

## Async Testing Tips

### Mark as async
Always use `@pytest.mark.asyncio` decorator for async tests:

```python
@pytest.mark.asyncio
async def test_async_function(self):
    result = await some_async_function()
    assert result is not None
```

### Mock async functions
Use `AsyncMock` for async mocked functions:

```python
from unittest.mock import AsyncMock

mock_func = AsyncMock(return_value="result")
result = await mock_func()
```

### Test async generators
For async generators, consume them:

```python
@pytest.mark.asyncio
async def test_async_generator(self):
    items = []
    async for item in my_async_gen():
        items.append(item)
    assert len(items) > 0
```

## Common Fixtures

| Fixture | Purpose |
|---------|---------|
| `mock_user` | Single Discord user |
| `mock_member` | Guild member with roles |
| `mock_guild` | Discord guild |
| `mock_channel` | Discord channel |
| `mock_ctx` | Command context |
| `mock_interaction` | Slash command interaction |
| `mock_bot` | Discord bot client |
| `mock_db` | MongoDB database |
| `mock_users_collection` | Users collection |
| `mock_rdw_games_collection` | RDW games collection |
| `mock_run_times_collection` | RDW runs collection |
| `mock_bets_collection` | Bets collection |

## Running Tests

```bash
# All tests
pytest tests/

# Specific file
pytest tests/test_formatting.py

# Specific class
pytest tests/test_formatting.py::TestFormatUsers

# Specific test
pytest tests/test_formatting.py::TestFormatUsers::test_single_user

# With output
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html

# Stop on first failure
pytest tests/ -x

# Show print statements
pytest tests/ -s
```

## Integration with Manual Testing

While automated tests handle logic verification, you can still:

1. **Unit tests** cover isolated functions and logic
2. **Integration tests** verify database operations work correctly
3. **Manual testing** with a test bot verifies Discord UI/interactions work as expected

Set up a test Discord server and test bot token for final verification before deploying to production.
