# Testing Guide for tip-time

This directory contains unit tests, integration tests, and fixtures for testing the tip-time Discord bot without manual end-to-end testing.

## Running Tests

### Install test dependencies
```bash
pip install -r requirements.txt
```

### Run all tests
```bash
pytest
```

### Run tests with verbose output
```bash
pytest -v
```

### Run a specific test file
```bash
pytest tests/test_formatting.py
```

### Run a specific test class
```bash
pytest tests/test_formatting.py::TestFormatUsers
```

### Run a specific test function
```bash
pytest tests/test_formatting.py::TestFormatUsers::test_single_user
```

### Run tests with coverage report
```bash
pip install pytest-cov
pytest --cov=. --cov-report=html
```

## Test Structure

### Fixtures (conftest.py)

The `conftest.py` file contains reusable fixtures for mocking Discord objects and MongoDB:

- **Discord Mocks**:
  - `mock_user`: A mock Discord user
  - `mock_member`: A mock Discord guild member
  - `mock_guild`: A mock Discord guild
  - `mock_channel`: A mock Discord channel
  - `mock_ctx`: A mock Discord context/command context
  - `mock_interaction`: A mock Discord interaction (for slash commands)
  - `mock_bot`: A mock Discord bot client

- **Database Fixtures**:
  - `mock_db`: A complete mocked MongoDB client (using mongomock)
  - `mock_users_collection`: Users collection
  - `mock_rdw_games_collection`: RDW games collection
  - `mock_run_times_collection`: RDW runs collection
  - `mock_bets_collection`: Bets collection

### Test Files

- **test_formatting.py**: Tests for utility functions (formatting, time parsing)
- **test_horse_race.py**: Tests for horse race game logic
- **test_db.py**: Integration tests for database operations
- **test_views.py**: Tests for Discord UI components (buttons, modals, selects)

## Writing New Tests

### Basic Unit Test

```python
import pytest
from my_module import my_function

class TestMyFunction:
    def test_basic_case(self):
        result = my_function(10)
        assert result == expected_value
    
    def test_edge_case(self):
        result = my_function(0)
        assert result == 0
```

### Test with Mocked Database

```python
def test_user_creation(self, mock_users_collection):
    # Insert a user
    user_doc = {"_id": 123, "name": "Alice", "coins": 500}
    mock_users_collection.insert_one(user_doc)
    
    # Fetch and verify
    result = mock_users_collection.find_one({"_id": 123})
    assert result["name"] == "Alice"
```

### Test with Mocked Discord Context

```python
@pytest.mark.asyncio
async def test_command_handler(self, mock_ctx):
    # Use the context to test a command
    await my_command_handler(mock_ctx)
    
    # Verify the bot responded
    mock_ctx.send.assert_called_once()
```

### Test Async Functions

```python
@pytest.mark.asyncio
async def test_async_function(self):
    result = await my_async_function()
    assert result is not None
```

## Key Testing Patterns

### Mocking Discord Interactions

For testing commands, use the `mock_ctx` or `mock_interaction` fixtures:

```python
def test_command_with_context(self, mock_ctx):
    # Modify the context as needed
    mock_ctx.author.id = 123456789
    mock_ctx.author.name = "TestUser"
    
    # Run your command
    # Your command code here
    
    # Verify the response
    assert mock_ctx.send.called
```

### Testing Database Operations

Use the collection fixtures to test CRUD operations:

```python
def test_save_and_retrieve(self, mock_users_collection):
    # Create
    mock_users_collection.insert_one({"_id": 1, "name": "Alice"})
    
    # Retrieve
    result = mock_users_collection.find_one({"_id": 1})
    
    # Update
    mock_users_collection.update_one({"_id": 1}, {'$set': {'name': 'Alice2'}})
    
    # Verify
    result = mock_users_collection.find_one({"_id": 1})
    assert result["name"] == "Alice2"
```

## MongoDB Testing with mongomock

The `mock_db` fixture uses [mongomock](https://github.com/mongomock/mongomock), which provides an in-memory MongoDB-like interface. This allows tests to:

- Run fast (no network overhead)
- Be isolated (no shared test database)
- Be deterministic (no timing issues)

mongomock supports most MongoDB operations:
- insert_one, insert_many
- find, find_one
- update_one, update_many
- delete_one, delete_many
- Aggregation pipelines (basic support)

## Manual Testing with Test Bot

While automated tests cover most scenarios, you may still want to manually test Discord interactions:

1. Create a test Discord server
2. Create a test bot with a test token
3. Run the bot in development mode
4. Interact with it in your test server

See the main README for bot setup instructions.

## Continuous Integration

To run tests automatically on every commit, you can set up a CI/CD pipeline (GitHub Actions, GitLab CI, etc.):

```yaml
# Example GitHub Actions workflow
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - run: pip install -r requirements.txt
      - run: pytest
```

## Troubleshooting

### Import Errors

If you get import errors, make sure the project root is in your PYTHONPATH:

```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/tip-time"
pytest
```

### Async Test Errors

If async tests fail with "no running event loop", ensure pytest-asyncio is installed and the `@pytest.mark.asyncio` decorator is used.

### MongoDB Connection Errors

Tests should not attempt to connect to a real MongoDB. If you see connection errors, check that:
- You're using the `mock_db` fixture
- The real MongoDB connection is not being initialized in the code being tested

## Adding Tests for Commands

To test command handlers in `bot_commands.py`, create mocked contexts and interactions:

```python
@pytest.mark.asyncio
async def test_addme_command(self, mock_ctx, mock_users_collection):
    # Mock the database
    with patch('bot_commands.user_collection', mock_users_collection):
        # Call your command
        await addme_command(mock_ctx)
        
        # Verify user was created
        user = mock_users_collection.find_one({"_id": mock_ctx.author.id})
        assert user is not None
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [mongomock Documentation](https://mongomock.readthedocs.io/)
- [py-cord Documentation](https://docs.pycord.dev/)
