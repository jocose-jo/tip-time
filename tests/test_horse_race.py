import pytest
from unittest.mock import MagicMock
from horse_race import get_random_unique_horses, trim_name, horse_map


class TestGetRandomUniqueHorses:
    def test_get_random_horses(self):
        mock_emojis = [
            MagicMock(name="horse_brown", id=1116114371446317100),
            MagicMock(name="horse_blue", id=1116123670683848775),
            MagicMock(name="horse_gold", id=1116123557253107832),
            MagicMock(name="other_emoji", id=999999999),
        ]
        result = get_random_unique_horses(mock_emojis, 2)

        assert len(result) == 2
        assert all(horse["id"] in horse_map.values() for horse in result)
        assert len(set(h["id"] for h in result)) == 2  # All unique

    def test_get_random_horses_single(self):
        mock_emojis = [
            MagicMock(name="horse_brown", id=1116114371446317100),
            MagicMock(name="horse_blue", id=1116123670683848775),
        ]
        result = get_random_unique_horses(mock_emojis, 1)

        assert len(result) == 1
        assert result[0]["id"] in horse_map.values()

    def test_get_random_horses_all_available(self):
        mock_emojis = [
            MagicMock(name=name, id=id)
            for name, id in horse_map.items()
        ]
        result = get_random_unique_horses(mock_emojis, 7)

        assert len(result) == 7
        assert len(set(h["id"] for h in result)) == 7

    def test_get_random_horses_filters_non_horses(self):
        mock_emojis = [
            MagicMock(name="horse_brown", id=1116114371446317100),
            MagicMock(name="other_emoji", id=999999999),
            MagicMock(name="another_emoji", id=888888888),
            MagicMock(name="horse_blue", id=1116123670683848775),
        ]
        result = get_random_unique_horses(mock_emojis, 2)

        assert len(result) == 2
        assert all(horse["id"] in horse_map.values() for horse in result)

    def test_get_random_horses_insufficient(self):
        mock_emojis = [
            MagicMock(name="horse_brown", id=1116114371446317100),
        ]
        with pytest.raises(ValueError):
            get_random_unique_horses(mock_emojis, 2)


class TestTrimName:
    def test_trim_short_name(self):
        result = trim_name("Hi", 5)
        assert result == "Hi   "
        assert len(result) == 5

    def test_trim_exact_length(self):
        result = trim_name("Hello", 5)
        assert result == "Hello"

    def test_trim_long_name(self):
        result = trim_name("HelloWorld", 5)
        assert result == "Hello"

    def test_trim_empty_string(self):
        result = trim_name("", 3)
        assert result == "   "
        assert len(result) == 3

    def test_trim_single_char(self):
        result = trim_name("A", 1)
        assert result == "A"

    def test_trim_single_char_pad(self):
        result = trim_name("A", 5)
        assert result == "A    "
