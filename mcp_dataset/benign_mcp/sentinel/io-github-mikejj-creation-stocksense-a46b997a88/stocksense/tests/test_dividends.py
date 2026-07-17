"""Tests for dividend data tool."""

import pytest

from stocksense.data.market import fetch_dividends
from stocksense.tools.dividends import get_dividends


class TestFetchDividends:
    def test_returns_valid_data(self):
        result = fetch_dividends("AAPL")
        assert result["ticker"] == "AAPL"
        assert "dividend_rate" in result
        assert "dividend_yield" in result
        assert "history" in result

    def test_history_structure(self):
        result = fetch_dividends("MSFT")
        if result["history"]:
            entry = result["history"][0]
            assert "date" in entry
            assert "amount" in entry
            assert isinstance(entry["amount"], float)

    def test_invalid_ticker(self):
        with pytest.raises((ValueError, RuntimeError)):
            fetch_dividends("INVALIDTICKER999XYZ")


class TestGetDividendsTool:
    def test_output_format(self):
        result = get_dividends("AAPL")
        assert result["ticker"] == "AAPL"
        assert "history" in result
        assert "payout_ratio" in result
