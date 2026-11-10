"""Tests for the dice roller MCP server."""

import pytest
from mcp_dice_roller.server import (
    roll_dice,
    roll_multiple,
    roll_dnd_stats,
    flip_coin,
    pick_random,
    roll_percentile,
)


class TestRollDice:
    """Tests for the roll_dice function."""

    def test_simple_roll(self):
        """Test basic dice roll."""
        result = roll_dice("1d6")
        assert "total" in result
        assert 1 <= result["total"] <= 6
        assert result["rolls"] == result["kept"]

    def test_multiple_dice(self):
        """Test rolling multiple dice."""
        result = roll_dice("3d6")
        assert len(result["rolls"]) == 3
        assert all(1 <= r <= 6 for r in result["rolls"])
        assert result["total"] == sum(result["rolls"])

    def test_with_positive_modifier(self):
        """Test dice roll with positive modifier."""
        result = roll_dice("1d6+5")
        assert result["modifier"] == 5
        assert result["total"] == result["subtotal"] + 5

    def test_with_negative_modifier(self):
        """Test dice roll with negative modifier."""
        result = roll_dice("1d6-2")
        assert result["modifier"] == -2
        assert result["total"] == result["subtotal"] - 2

    def test_keep_highest(self):
        """Test keeping highest dice."""
        result = roll_dice("4d6kh3")
        assert len(result["rolls"]) == 4
        assert len(result["kept"]) == 3
        assert len(result["dropped"]) == 1
        # Kept should be the highest 3
        assert min(result["kept"]) >= max(result["dropped"])

    def test_keep_lowest(self):
        """Test keeping lowest dice."""
        result = roll_dice("2d20kl1")
        assert len(result["rolls"]) == 2
        assert len(result["kept"]) == 1
        assert len(result["dropped"]) == 1
        # Kept should be the lowest
        assert result["kept"][0] <= result["dropped"][0]

    def test_d20(self):
        """Test d20 roll."""
        result = roll_dice("1d20")
        assert 1 <= result["total"] <= 20

    def test_invalid_notation(self):
        """Test invalid dice notation."""
        result = roll_dice("invalid")
        assert "error" in result

    def test_too_many_dice(self):
        """Test rolling too many dice."""
        result = roll_dice("101d6")
        assert "error" in result

    def test_invalid_sides(self):
        """Test invalid die sides."""
        result = roll_dice("1d1")
        assert "error" in result


class TestRollMultiple:
    """Tests for the roll_multiple function."""

    def test_multiple_rolls(self):
        """Test rolling multiple times."""
        result = roll_multiple("1d6", 5)
        assert result["times"] == 5
        assert len(result["results"]) == 5
        assert len(result["totals"]) == 5

    def test_statistics(self):
        """Test statistics calculation."""
        result = roll_multiple("1d6", 10)
        stats = result["statistics"]
        assert stats["min"] == min(result["totals"])
        assert stats["max"] == max(result["totals"])
        assert stats["sum"] == sum(result["totals"])

    def test_too_many_times(self):
        """Test rolling too many times."""
        result = roll_multiple("1d6", 25)
        assert "error" in result


class TestRollDndStats:
    """Tests for the roll_dnd_stats function."""

    def test_six_stats(self):
        """Test that 6 stats are generated."""
        result = roll_dnd_stats()
        assert len(result["stats"]) == 6
        assert len(result["totals"]) == 6

    def test_stat_range(self):
        """Test that stats are in valid range (3-18)."""
        result = roll_dnd_stats()
        for total in result["totals"]:
            assert 3 <= total <= 18

    def test_four_dice_rolled(self):
        """Test that 4 dice are rolled for each stat."""
        result = roll_dnd_stats()
        for stat in result["stats"]:
            assert len(stat["rolls"]) == 4
            assert len(stat["kept"]) == 3


class TestFlipCoin:
    """Tests for the flip_coin function."""

    def test_single_flip(self):
        """Test single coin flip."""
        result = flip_coin(1)
        assert result["result"] in ["heads", "tails"]

    def test_multiple_flips(self):
        """Test multiple coin flips."""
        result = flip_coin(10)
        assert len(result["flips"]) == 10
        assert result["count"]["heads"] + result["count"]["tails"] == 10

    def test_too_many_flips(self):
        """Test flipping too many times."""
        result = flip_coin(101)
        assert "error" in result


class TestPickRandom:
    """Tests for the pick_random function."""

    def test_pick_from_list(self):
        """Test picking from a list."""
        result = pick_random("a, b, c")
        assert result["selected"] in ["a", "b", "c"]
        assert result["total_options"] == 3

    def test_not_enough_options(self):
        """Test with insufficient options."""
        result = pick_random("only_one")
        assert "error" in result

    def test_whitespace_handling(self):
        """Test that whitespace is handled."""
        result = pick_random("  a  ,  b  ,  c  ")
        assert result["options"] == ["a", "b", "c"]


class TestRollPercentile:
    """Tests for the roll_percentile function."""

    def test_percentile_range(self):
        """Test percentile is in valid range."""
        result = roll_percentile()
        assert 1 <= result["result"] <= 100

    def test_dice_values(self):
        """Test tens and ones dice are valid."""
        result = roll_percentile()
        assert 0 <= result["tens_die"] <= 10
        assert 0 <= result["ones_die"] <= 10
