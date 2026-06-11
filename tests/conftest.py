import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator

import pytest
from mongomock import MongoClient as MockMongoClient

# Discord mocks
class MockUser:
    def __init__(self, id: int = 123456789, name: str = "TestUser"):
        self.id = id
        self.name = name
        self.mention = f"<@{id}>"
        self.display_name = name

class MockMember(MockUser):
    def __init__(self, id: int = 123456789, name: str = "TestUser"):
        super().__init__(id, name)
        self.roles = []

class MockGuild:
    def __init__(self, id: int = 987654321, name: str = "TestGuild"):
        self.id = id
        self.name = name
        self.members = []

class MockChannel:
    def __init__(self, id: int = 111222333, name: str = "test-channel"):
        self.id = id
        self.name = name
        self.guild = MockGuild()
        self.send = AsyncMock()

class MockContext:
    def __init__(self, user: MockUser = None, guild: MockGuild = None, channel: MockChannel = None):
        self.author = user or MockUser()
        self.guild = guild or MockGuild()
        self.channel = channel or MockChannel()
        self.send = AsyncMock()
        self.respond = AsyncMock()
        self.interaction = None

class MockInteraction:
    def __init__(self, user: MockUser = None):
        self.user = user or MockUser()
        self.response = AsyncMock()
        self.response.send_message = AsyncMock()
        self.response.defer = AsyncMock()

# Fixtures
@pytest.fixture
def mock_user():
    return MockUser()

@pytest.fixture
def mock_member():
    return MockMember()

@pytest.fixture
def mock_guild():
    return MockGuild()

@pytest.fixture
def mock_channel():
    return MockChannel()

@pytest.fixture
def mock_ctx(mock_user, mock_guild, mock_channel):
    ctx = MockContext(user=mock_user, guild=mock_guild, channel=mock_channel)
    return ctx

@pytest.fixture
def mock_interaction(mock_user):
    return MockInteraction(user=mock_user)

@pytest.fixture
def mock_db():
    """Fixture providing a mocked MongoDB client using mongomock."""
    client = MockMongoClient()
    db = client['tip_time_test']
    return db

@pytest.fixture
def mock_users_collection(mock_db):
    """Fixture for the Users collection."""
    return mock_db['Users']

@pytest.fixture
def mock_rdw_games_collection(mock_db):
    """Fixture for the RDWGames collection."""
    return mock_db['RDWGames']

@pytest.fixture
def mock_run_times_collection(mock_db):
    """Fixture for the RunTimes collection."""
    return mock_db['RunTimes']

@pytest.fixture
def mock_bets_collection(mock_db):
    """Fixture for the Bets collection."""
    return mock_db['Bets']

@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def mock_bot():
    """Fixture for a mocked Discord bot client."""
    bot = AsyncMock()
    bot.user = MockUser(id=999999999, name="TestBot")
    bot.get_user = AsyncMock(return_value=MockUser())
    bot.get_guild = AsyncMock(return_value=MockGuild())
    return bot
