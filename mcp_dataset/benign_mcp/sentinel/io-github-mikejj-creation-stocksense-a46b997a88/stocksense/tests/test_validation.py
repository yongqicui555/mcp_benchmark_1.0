"""Tests for input validation."""

import pytest

from stocksense.tools.validation import (
    validate_interval,
    validate_limit,
    validate_period,
    validate_statement,
    validate_ticker,
)


class TestValidateTicker:
    def test_valid_tickers(self):
        assert validate_ticker("AAPL") == "AAPL"
        assert validate_ticker("aapl") == "AAPL"
        assert validate_ticker("MSFT") == "MSFT"
        assert validate_ticker("A") == "A"

    def test_ticker_with_dot(self):
        assert validate_ticker("BRK.B") == "BRK.B"

    def test_ticker_with_dash(self):
        assert validate_ticker("BRK-B") == "BRK-B"

    def test_strips_whitespace(self):
        assert validate_ticker("  AAPL  ") == "AAPL"

    def test_empty_ticker(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_ticker("")

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid ticker format"):
            validate_ticker("123456")

    def test_too_long(self):
        with pytest.raises(ValueError, match="Invalid ticker format"):
            validate_ticker("TOOLONGTICKER")


class TestValidatePeriod:
    def test_valid_periods(self):
        for p in ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"]:
            assert validate_period(p) == p

    def test_invalid_period(self):
        with pytest.raises(ValueError, match="Invalid period"):
            validate_period("10y")


class TestValidateInterval:
    def test_valid_intervals(self):
        for i in ["1m", "5m", "15m", "1h", "1d", "1wk", "1mo"]:
            assert validate_interval(i) == i

    def test_invalid_interval(self):
        with pytest.raises(ValueError, match="Invalid interval"):
            validate_interval("2h")


class TestValidateStatement:
    def test_valid_statements(self):
        for s in ["income", "balance_sheet", "cash_flow", "all"]:
            assert validate_statement(s) == s

    def test_invalid_statement(self):
        with pytest.raises(ValueError, match="Invalid statement"):
            validate_statement("nonsense")


class TestValidateLimit:
    def test_valid_limits(self):
        assert validate_limit(1) == 1
        assert validate_limit(50) == 50
        assert validate_limit(100) == 100

    def test_zero_limit(self):
        with pytest.raises(ValueError, match="at least 1"):
            validate_limit(0)

    def test_negative_limit(self):
        with pytest.raises(ValueError, match="at least 1"):
            validate_limit(-5)

    def test_exceeds_max(self):
        with pytest.raises(ValueError, match="cannot exceed"):
            validate_limit(101)

    def test_custom_max(self):
        assert validate_limit(50, max_limit=50) == 50
        with pytest.raises(ValueError, match="cannot exceed"):
            validate_limit(51, max_limit=50)
