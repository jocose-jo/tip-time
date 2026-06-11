import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from views import GameButton, GameView


class TestGameButton:
    """Test GameButton Discord component."""

    def test_game_button_initialization(self):
        """Test that GameButton initializes with correct attributes."""
        button_id = 100
        run_id = 1234567890
        game_data = {
            "name": "Mario Kart",
            "status": "PENDING",
            "start": None,
            "end": None
        }
        button = GameButton(button_id, run_id, game_data)

        assert button.label == "Mario Kart"
        assert button.run_id == run_id
        assert button.name == "Mario Kart"
        assert button.status == "PENDING"

    def test_game_button_custom_id(self):
        """Test that custom_id is properly formatted."""
        button_id = 200
        run_id = 9876543210
        game_data = {
            "name": "Smash Bros",
            "status": "PENDING",
            "start": None,
            "end": None
        }
        button = GameButton(button_id, run_id, game_data)

        # custom_id should include the game name and button_id
        assert "Smash Bros" in button.custom_id
        assert str(button_id) in button.custom_id

    def test_game_button_disabled_when_complete(self):
        """Test that button is disabled when game is complete."""
        button_id = 150
        run_id = 1111111111
        game_data = {
            "name": "Game",
            "status": "COMPLETE",
            "start": None,
            "end": None
        }
        button = GameButton(button_id, run_id, game_data)

        assert button.disabled is True

    def test_game_button_enabled_when_pending(self):
        """Test that button is enabled when game is pending."""
        button_id = 160
        run_id = 2222222222
        game_data = {
            "name": "Game",
            "status": "PENDING",
            "start": None,
            "end": None
        }
        button = GameButton(button_id, run_id, game_data)

        assert button.disabled is False


class TestGameView:
    """Test GameView Discord component."""

    @patch('views.fetch_rdw_run_or_create')
    def test_game_view_initialization(self, mock_fetch):
        """Test that GameView initializes with run data."""
        # Mock the database call
        mock_run_data = {
            "_id": 1234567890,
            "users": ["Alice", "Bob"],
            "status": "IN-PROGRESS",
            "game_data": [
                {"name": "Mario Kart", "status": "PENDING", "start": None, "end": None},
                {"name": "Smash Bros", "status": "PENDING", "start": None, "end": None},
            ]
        }
        mock_fetch.return_value = mock_run_data

        view = GameView(run_id=1234567890, users=[])

        assert view is not None
        # View should have children (buttons) for each game
        assert len(view.children) == 2

    @patch('views.fetch_rdw_run_or_create')
    def test_game_view_contains_all_games(self, mock_fetch):
        """Test that GameView creates buttons for all games."""
        mock_run_data = {
            "_id": 9999999999,
            "users": ["User1"],
            "status": "IN-PROGRESS",
            "game_data": [
                {"name": "Game A", "status": "PENDING", "start": None, "end": None},
                {"name": "Game B", "status": "PENDING", "start": None, "end": None},
                {"name": "Game C", "status": "PENDING", "start": None, "end": None},
            ]
        }
        mock_fetch.return_value = mock_run_data

        view = GameView(run_id=9999999999, users=[])

        labels = [child.label for child in view.children if hasattr(child, 'label')]
        assert len(labels) == 3
        assert "Game A" in labels
        assert "Game B" in labels
        assert "Game C" in labels
