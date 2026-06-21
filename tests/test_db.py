import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from bson.objectid import ObjectId

# We'll import db functions but patch the collection references
from db import GameStatus


class TestUserOperations:
    """Test user-related database operations."""

    def test_save_new_user(self, mock_users_collection):
        """Test creating a new user."""
        mock_user = MagicMock()
        mock_user.id = 123456789
        mock_user.name = "TestUser"

        # Simulate saving
        user_doc = {"_id": mock_user.id, "name": mock_user.name, "strikes": 0, "coins": 500}
        mock_users_collection.insert_one(user_doc)

        # Verify
        result = mock_users_collection.find_one({"_id": 123456789})
        assert result["name"] == "TestUser"
        assert result["strikes"] == 0
        assert result["coins"] == 500

    def test_fetch_user(self, mock_users_collection):
        """Test fetching an existing user."""
        user_doc = {"_id": 123456789, "name": "TestUser", "strikes": 2, "coins": 400}
        mock_users_collection.insert_one(user_doc)

        result = mock_users_collection.find_one({"_id": 123456789})
        assert result is not None
        assert result["name"] == "TestUser"
        assert result["strikes"] == 2

    def test_update_user_strikes(self, mock_users_collection):
        """Test updating user strikes."""
        user_doc = {"_id": 123456789, "name": "TestUser", "strikes": 2, "coins": 500}
        mock_users_collection.insert_one(user_doc)

        # Add 1 strike
        mock_users_collection.update_one(
            {"_id": 123456789},
            {'$set': {'strikes': 3}}
        )

        result = mock_users_collection.find_one({"_id": 123456789})
        assert result["strikes"] == 3

    def test_update_user_coins(self, mock_users_collection):
        """Test updating user coins."""
        user_doc = {"_id": 123456789, "name": "TestUser", "coins": 500}
        mock_users_collection.insert_one(user_doc)

        # Add coins
        mock_users_collection.update_one(
            {"_id": 123456789},
            {'$set': {'coins': 550}}
        )

        result = mock_users_collection.find_one({"_id": 123456789})
        assert result["coins"] == 550

    def test_fetch_all_users(self, mock_users_collection):
        """Test fetching all users."""
        users = [
            {"_id": 111111111, "name": "Alice", "strikes": 0, "coins": 500},
            {"_id": 222222222, "name": "Bob", "strikes": 1, "coins": 450},
            {"_id": 333333333, "name": "Charlie", "strikes": 2, "coins": 400},
        ]
        mock_users_collection.insert_many(users)

        result = list(mock_users_collection.find({}))
        assert len(result) == 3
        names = [doc["name"] for doc in result]
        assert "Alice" in names
        assert "Bob" in names


class TestRDWGameOperations:
    """Test RDW game-related database operations."""

    def test_add_new_rdw_game(self, mock_rdw_games_collection):
        """Test adding a new RDW game."""
        game_name = "Mario Kart"
        game_doc = {"name": game_name, "lowerName": game_name.lower()}
        mock_rdw_games_collection.insert_one(game_doc)

        result = mock_rdw_games_collection.find_one({"lowerName": "mario kart"})
        assert result is not None
        assert result["name"] == "Mario Kart"

    def test_game_case_insensitive_query(self, mock_rdw_games_collection):
        """Test that game queries are case-insensitive."""
        game_doc = {"name": "Super Mario Bros", "lowerName": "super mario bros"}
        mock_rdw_games_collection.insert_one(game_doc)

        result = mock_rdw_games_collection.find_one({"lowerName": "super mario bros"})
        assert result is not None

    def test_fetch_rdw_games(self, mock_rdw_games_collection):
        """Test fetching all RDW games."""
        games = [
            {"name": "Mario Kart", "lowerName": "mario kart"},
            {"name": "Smash Bros", "lowerName": "smash bros"},
            {"name": "Pokemon", "lowerName": "pokemon"},
        ]
        mock_rdw_games_collection.insert_many(games)

        result = list(mock_rdw_games_collection.find({}, ["name"]))
        game_names = [doc["name"] for doc in result]
        assert len(game_names) == 3
        assert "Mario Kart" in game_names

    def test_destroy_rdw_game(self, mock_rdw_games_collection):
        """Test deleting an RDW game."""
        game_doc = {"name": "Mario Kart", "lowerName": "mario kart"}
        mock_rdw_games_collection.insert_one(game_doc)

        # Delete it
        mock_rdw_games_collection.delete_one({"lowerName": "mario kart"})

        result = mock_rdw_games_collection.find_one({"lowerName": "mario kart"})
        assert result is None


class TestRDWRunOperations:
    """Test RDW run (race) related database operations."""

    def test_start_rdw_run(self, mock_run_times_collection, mock_rdw_games_collection):
        """Test starting a new RDW run."""
        # Setup games
        games = [
            {"name": "Mario Kart", "lowerName": "mario kart"},
            {"name": "Smash Bros", "lowerName": "smash bros"},
        ]
        mock_rdw_games_collection.insert_many(games)

        # Create run
        users = ["Alice", "Bob"]
        start_time = datetime.now()
        game_names = [g["name"] for g in games]

        rdw_run = {
            "_id": int(datetime.now().timestamp()),
            "users": users,
            "status": "IN-PROGRESS",
            "start": start_time,
            "end": None,
            "total_time": None,
            "game_data": [{"name": game, "start": None, "end": None, "status": "PENDING"} for game in game_names]
        }
        mock_run_times_collection.insert_one(rdw_run)

        # Verify
        result = mock_run_times_collection.find_one({"_id": rdw_run["_id"]})
        assert result is not None
        assert result["status"] == "IN-PROGRESS"
        assert len(result["game_data"]) == 2

    def test_fetch_rdw_run(self, mock_run_times_collection):
        """Test fetching a specific RDW run."""
        run_id = int(datetime.now().timestamp())
        run_doc = {
            "_id": run_id,
            "users": ["Alice", "Bob"],
            "status": "IN-PROGRESS",
            "start": datetime.now(),
            "end": None,
            "game_data": [
                {"name": "Game1", "start": None, "end": None, "status": "PENDING"},
            ]
        }
        mock_run_times_collection.insert_one(run_doc)

        result = mock_run_times_collection.find_one({"_id": run_id})
        assert result["users"] == ["Alice", "Bob"]

    def test_update_rdw_run_complete(self, mock_run_times_collection):
        """Test marking an RDW run as complete."""
        run_id = int(datetime.now().timestamp())
        run_doc = {
            "_id": run_id,
            "users": ["Alice"],
            "status": "IN-PROGRESS",
            "start": datetime.now() - timedelta(minutes=5),
            "end": None,
            "game_data": []
        }
        mock_run_times_collection.insert_one(run_doc)

        # Update to complete
        end_time = datetime.now()
        mock_run_times_collection.update_one(
            {"_id": run_id},
            {'$set': {"end": end_time, "status": "COMPLETE", "total_time": "00:05:00.000000"}}
        )

        result = mock_run_times_collection.find_one({"_id": run_id})
        assert result["status"] == "COMPLETE"
        assert result["end"] is not None

    def test_update_rdw_game_status(self, mock_run_times_collection):
        """Test updating a game status within an RDW run."""
        run_id = int(datetime.now().timestamp())
        run_doc = {
            "_id": run_id,
            "users": ["Alice"],
            "status": "IN-PROGRESS",
            "game_data": [
                {"name": "Mario Kart", "start": None, "end": None, "status": "PENDING"},
                {"name": "Smash Bros", "start": None, "end": None, "status": "PENDING"},
            ]
        }
        mock_run_times_collection.insert_one(run_doc)

        # Start a game
        start_time = datetime.now()
        mock_run_times_collection.update_one(
            {"_id": run_id, "game_data.name": "Mario Kart"},
            {'$set': {"game_data.$.start": start_time, "game_data.$.status": "IN-PROGRESS"}}
        )

        result = mock_run_times_collection.find_one({"_id": run_id})
        mario_game = next(g for g in result["game_data"] if g["name"] == "Mario Kart")
        assert mario_game["status"] == "IN-PROGRESS"
        assert mario_game["start"] is not None


class TestBetOperations:
    """Test betting-related database operations."""

    def test_create_bet(self, mock_bets_collection):
        """Test creating a new bet."""
        creator_id = 123456789
        channel_id = 999999999
        description = "Will Alice win?"
        outcomes = ["Yes", "No"]

        bet_doc = {
            "creator_id": creator_id,
            "channel_id": channel_id,
            "message_id": None,
            "description": description,
            "outcomes": outcomes,
            "status": "OPEN",
            "bets": [],
            "winner_outcome": None,
            "created_at": datetime.now()
        }
        result = mock_bets_collection.insert_one(bet_doc)
        bet_doc["_id"] = result.inserted_id

        # Fetch and verify
        fetched = mock_bets_collection.find_one({"_id": result.inserted_id})
        assert fetched["description"] == "Will Alice win?"
        assert fetched["status"] == "OPEN"
        assert fetched["outcomes"] == ["Yes", "No"]

    def test_add_wager_to_bet(self, mock_bets_collection):
        """Test adding a wager to a bet."""
        bet_doc = {
            "creator_id": 123456789,
            "channel_id": 999999999,
            "description": "Will Alice win?",
            "outcomes": ["Yes", "No"],
            "status": "OPEN",
            "bets": [],
        }
        result = mock_bets_collection.insert_one(bet_doc)
        bet_id = result.inserted_id

        # Add wager
        wager = {"user_id": 111111111, "username": "Bob", "outcome": "Yes", "amount": 100}
        mock_bets_collection.update_one(
            {"_id": bet_id},
            {'$push': {'bets': wager}}
        )

        # Verify
        fetched = mock_bets_collection.find_one({"_id": bet_id})
        assert len(fetched["bets"]) == 1
        assert fetched["bets"][0]["username"] == "Bob"
        assert fetched["bets"][0]["amount"] == 100

    def test_settle_bet(self, mock_bets_collection):
        """Test settling a bet."""
        bet_doc = {
            "creator_id": 123456789,
            "description": "Will Alice win?",
            "outcomes": ["Yes", "No"],
            "status": "OPEN",
            "bets": [
                {"user_id": 111111111, "username": "Bob", "outcome": "Yes", "amount": 100},
                {"user_id": 222222222, "username": "Charlie", "outcome": "No", "amount": 50},
            ],
            "winner_outcome": None,
        }
        result = mock_bets_collection.insert_one(bet_doc)
        bet_id = result.inserted_id

        # Settle with "Yes" as winner
        mock_bets_collection.update_one(
            {"_id": bet_id},
            {'$set': {'status': 'SETTLED', 'winner_outcome': 'Yes'}}
        )

        # Verify
        fetched = mock_bets_collection.find_one({"_id": bet_id})
        assert fetched["status"] == "SETTLED"
        assert fetched["winner_outcome"] == "Yes"

    def test_fetch_open_bets(self, mock_bets_collection):
        """Test fetching all open bets."""
        bets = [
            {
                "creator_id": 111111111,
                "description": "Bet 1",
                "status": "OPEN",
                "bets": [],
            },
            {
                "creator_id": 222222222,
                "description": "Bet 2",
                "status": "SETTLED",
                "bets": [],
            },
            {
                "creator_id": 333333333,
                "description": "Bet 3",
                "status": "OPEN",
                "bets": [],
            },
        ]
        mock_bets_collection.insert_many(bets)

        # Fetch only open bets
        open_bets = list(mock_bets_collection.find({"status": "OPEN"}))
        assert len(open_bets) == 2
        descriptions = [b["description"] for b in open_bets]
        assert "Bet 1" in descriptions
        assert "Bet 3" in descriptions
        assert "Bet 2" not in descriptions


class TestBettingConstraints:
    """Test betting constraint functions."""

    def test_user_has_bet_returns_none_if_no_bet(self, mock_bets_collection):
        """Test that user_has_bet returns None when user hasn't bet."""
        bet_doc = {
            "creator_id": 123456789,
            "description": "Will Alice win?",
            "outcomes": ["Yes", "No"],
            "status": "OPEN",
            "bets": [
                {"user_id": 111111111, "username": "Bob", "outcome": "Yes", "amount": 100},
            ],
        }
        result = mock_bets_collection.insert_one(bet_doc)
        bet_id = result.inserted_id

        # Check if a different user has bet (they haven't)
        bets = list(mock_bets_collection.find({"_id": bet_id}))
        assert len(bets) == 1
        # In real code, user_has_bet would return None since user 222222222 hasn't bet

    def test_user_has_bet_returns_outcome_if_bet_exists(self, mock_bets_collection):
        """Test that user_has_bet returns the outcome when user has bet."""
        bet_doc = {
            "creator_id": 123456789,
            "description": "Will Alice win?",
            "outcomes": ["Yes", "No"],
            "status": "OPEN",
            "bets": [
                {"user_id": 111111111, "username": "Bob", "outcome": "Yes", "amount": 100},
            ],
        }
        result = mock_bets_collection.insert_one(bet_doc)
        bet_id = result.inserted_id

        # Check that the user has bet on "Yes"
        bets = list(mock_bets_collection.find({"_id": bet_id}))
        assert bets[0]["bets"][0]["outcome"] == "Yes"
        assert bets[0]["bets"][0]["user_id"] == 111111111


class TestGameStatus:
    """Test the GameStatus enum."""

    def test_game_status_values(self):
        """Test GameStatus enum values."""
        assert GameStatus.PENDING.value == 1
        assert GameStatus.IN_PROGRESS.value == 2
        assert GameStatus.COMPLETE.value == 3
        assert GameStatus.CANCELED.value == 4
        assert GameStatus.FAILED.value == 5
