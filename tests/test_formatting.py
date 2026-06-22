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
    format_duration,
    calculate_rdw_reward,
    format_team_mentions,
    format_team_summary,
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


class TestFormatDuration:
    def test_seconds_only(self):
        duration = timedelta(seconds=45)
        assert format_duration(duration) == "45 seconds"

    def test_minutes_and_seconds(self):
        duration = timedelta(minutes=5, seconds=30)
        result = format_duration(duration)
        assert "5 min" in result
        assert "30 second" in result

    def test_hours_minutes_seconds(self):
        duration = timedelta(hours=2, minutes=30, seconds=15)
        result = format_duration(duration)
        assert "2 hr" in result
        assert "30 min" in result
        assert "15 second" in result

    def test_single_hour(self):
        duration = timedelta(hours=1)
        assert "1 hr" in format_duration(duration)
        assert "hrs" not in format_duration(duration)

    def test_single_minute(self):
        duration = timedelta(minutes=1)
        assert "1 min" in format_duration(duration)

    def test_zero_duration(self):
        duration = timedelta()
        assert format_duration(duration) == "0 seconds"


class TestCalculateRDWReward:
    def test_under_3_hours_gets_250(self):
        duration = timedelta(hours=2, minutes=59)
        assert calculate_rdw_reward(duration) == 250

    def test_exactly_3_hours_gets_200(self):
        duration = timedelta(hours=3, minutes=0)
        assert calculate_rdw_reward(duration) == 200

    def test_between_3_and_4_hours_gets_200(self):
        duration = timedelta(hours=3, minutes=30)
        assert calculate_rdw_reward(duration) == 200

    def test_exactly_4_hours_gets_100(self):
        duration = timedelta(hours=4, minutes=0)
        assert calculate_rdw_reward(duration) == 100

    def test_over_4_hours_gets_100(self):
        duration = timedelta(hours=5, minutes=15)
        assert calculate_rdw_reward(duration) == 100

    def test_just_under_3_hours(self):
        duration = timedelta(hours=2, minutes=59, seconds=59)
        assert calculate_rdw_reward(duration) == 250

    def test_just_over_3_hours(self):
        duration = timedelta(hours=3, minutes=0, seconds=1)
        assert calculate_rdw_reward(duration) == 200

    def test_just_under_4_hours(self):
        duration = timedelta(hours=3, minutes=59, seconds=59)
        assert calculate_rdw_reward(duration) == 200

    def test_just_over_4_hours(self):
        duration = timedelta(hours=4, minutes=0, seconds=1)
        assert calculate_rdw_reward(duration) == 100


class TestFormatUsersSingleUser:
    """Test format_users with single user (newly fixed)."""

    def test_single_user_no_and(self):
        users = [{"name": "Alice"}]
        result = format_users(users)
        assert result == "Alice"
        assert ", and" not in result

    def test_empty_users(self):
        users = []
        result = format_users(users)
        assert result == ""

    def test_two_users_proper_format(self):
        users = [{"name": "Alice"}, {"name": "Bob"}]
        result = format_users(users)
        assert result == " Alice, and Bob"
        assert "Alice" in result
        assert "Bob" in result


class TestFormatTeamMentions:
    """Test format_team_mentions for different team sizes."""

    def test_solo_run(self):
        result = format_team_mentions("<@123>", [])
        assert result == "<@123>"

    def test_duo_run(self):
        result = format_team_mentions("<@123>", ["<@456>"])
        assert result == "<@123> and <@456>"

    def test_trio_run(self):
        result = format_team_mentions("<@123>", ["<@456>", "<@789>"])
        assert result == "<@123>, <@456>, and <@789>"

    def test_solo_with_empty_list(self):
        result = format_team_mentions("Alice", [])
        assert result == "Alice"

    def test_duo_formatting(self):
        result = format_team_mentions("Alice", ["Bob"])
        assert " and " in result
        assert "Alice" in result
        assert "Bob" in result


class TestFormatTeamSummary:
    """Test format_team_summary with mock discord users."""

    def test_solo_run_summary(self):
        selected_users = []
        run_type, team_display = format_team_summary(selected_users, "Alice")
        assert run_type == "👤 Solo Run"
        assert "Alice" in team_display
        assert "Team: Alice" == team_display

    def test_duo_run_summary(self):
        # Mock user objects
        class MockUser:
            def __init__(self, name):
                self.name = name

        selected_users = [MockUser("Bob")]
        run_type, team_display = format_team_summary(selected_users, "Alice")
        assert run_type == "👥 Duo Run"
        assert "Alice" in team_display
        assert "Bob" in team_display
        assert "+" in team_display

    def test_trio_run_summary(self):
        class MockUser:
            def __init__(self, name):
                self.name = name

        selected_users = [MockUser("Bob"), MockUser("Charlie")]
        run_type, team_display = format_team_summary(selected_users, "Alice")
        assert run_type == "👨‍👩‍👧 Trio Run"
        assert "Alice" in team_display
        assert "Bob" in team_display
        assert "Charlie" in team_display
        assert "+" in team_display

    def test_team_summary_initiator_name_used(self):
        selected_users = []
        _, team_display = format_team_summary(selected_users, "TestUser")
        assert "TestUser" in team_display

    def test_duo_summary_uses_correct_emoji(self):
        class MockUser:
            def __init__(self, name):
                self.name = name

        selected_users = [MockUser("Bob")]
        run_type, _ = format_team_summary(selected_users, "Alice")
        assert "👥" in run_type
        assert "Duo Run" in run_type

    def test_trio_summary_uses_correct_emoji(self):
        class MockUser:
            def __init__(self, name):
                self.name = name

        selected_users = [MockUser("Bob"), MockUser("Charlie")]
        run_type, _ = format_team_summary(selected_users, "Alice")
        assert "👨‍👩‍👧" in run_type
        assert "Trio Run" in run_type
