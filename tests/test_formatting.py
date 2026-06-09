import pytest
from datetime import datetime, timedelta
from formatting import (
    format_users,
    format_date,
    format_time_delta,
    format_date_time,
    calculate_in_game_time,
    convert_to_table,
    format_bet_summary,
)


class TestFormatUsers:
    def test_single_user(self):
        users = [{"name": "Alice"}]
        assert format_users(users) == ", and Alice"

    def test_two_users(self):
        users = [{"name": "Alice"}, {"name": "Bob"}]
        assert format_users(users) == " Alice, and Bob"

    def test_multiple_users(self):
        users = [
            {"name": "Alice"},
            {"name": "Bob"},
            {"name": "Charlie"}
        ]
        result = format_users(users)
        assert "Alice" in result
        assert "Bob" in result
        assert "Charlie" in result
        assert ", and" in result


class TestFormatDate:
    def test_format_date(self):
        date = datetime(2024, 6, 8, 14, 30, 45)
        result = format_date(date)
        assert result == "06-08-2024 @02:30 PM"

    def test_format_date_midnight(self):
        date = datetime(2024, 1, 1, 0, 0, 0)
        result = format_date(date)
        assert result == "01-01-2024 @12:00 AM"


class TestFormatTimeDelta:
    def test_format_time_delta(self):
        time_str = "01:30:45.123456"
        result = format_time_delta(time_str)
        assert result == "01:30:45.123456"

    def test_format_time_delta_zero(self):
        time_str = "00:00:00.000000"
        result = format_time_delta(time_str)
        assert result == "00:00:00.000000"


class TestFormatDateTime:
    def test_format_date_time_removes_ms(self):
        date_str = "01:30:45.123456"
        result = format_date_time(date_str)
        assert result == "01:30:45"
        assert "." not in result

    def test_format_date_time_midnight(self):
        date_str = "00:00:00.000000"
        result = format_date_time(date_str)
        assert result == "00:00:00"


class TestCalculateInGameTime:
    def test_single_game(self):
        game_data = [
            {
                "start": datetime(2024, 1, 1, 10, 0, 0),
                "end": datetime(2024, 1, 1, 10, 5, 0),
            }
        ]
        result = calculate_in_game_time(game_data)
        assert result == timedelta(minutes=5)

    def test_multiple_games(self):
        game_data = [
            {
                "start": datetime(2024, 1, 1, 10, 0, 0),
                "end": datetime(2024, 1, 1, 10, 5, 0),
            },
            {
                "start": datetime(2024, 1, 1, 10, 10, 0),
                "end": datetime(2024, 1, 1, 10, 15, 0),
            },
        ]
        result = calculate_in_game_time(game_data)
        assert result == timedelta(minutes=10)

    def test_empty_game_data(self):
        game_data = []
        result = calculate_in_game_time(game_data)
        assert result == timedelta(0)


class TestConvertToTable:
    def test_simple_table(self):
        header = ["Name", "Score"]
        data = [["Alice", "100"], ["Bob", "200"]]
        result = convert_to_table(header, data)
        assert "Name" in result
        assert "Score" in result
        assert "Alice" in result
        assert "Bob" in result

    def test_empty_table(self):
        header = ["Name", "Score"]
        data = []
        result = convert_to_table(header, data)
        assert "Name" in result
        assert "Score" in result


class TestFormatBetSummary:
    def test_single_outcome_single_bet(self):
        bet = {
            "outcomes": ["Heads"],
            "bets": [{"outcome": "Heads", "username": "Alice", "amount": 100}]
        }
        result = format_bet_summary(bet)
        assert "Heads: 100" in result
        assert "Alice" in result

    def test_multiple_outcomes(self):
        bet = {
            "outcomes": ["Heads", "Tails"],
            "bets": [
                {"outcome": "Heads", "username": "Alice", "amount": 100},
                {"outcome": "Tails", "username": "Bob", "amount": 50},
            ]
        }
        result = format_bet_summary(bet)
        assert "Heads: 100" in result
        assert "Tails: 50" in result
        assert "Alice" in result
        assert "Bob" in result

    def test_no_bets_on_outcome(self):
        bet = {
            "outcomes": ["Heads", "Tails"],
            "bets": [{"outcome": "Heads", "username": "Alice", "amount": 100}]
        }
        result = format_bet_summary(bet)
        assert "Heads: 100" in result
        assert "Tails: 0" in result
        assert "No bets" in result

    def test_multiple_bets_same_outcome(self):
        bet = {
            "outcomes": ["Heads"],
            "bets": [
                {"outcome": "Heads", "username": "Alice", "amount": 100},
                {"outcome": "Heads", "username": "Bob", "amount": 50},
            ]
        }
        result = format_bet_summary(bet)
        assert "Heads: 150" in result
        assert "Alice" in result
        assert "Bob" in result
