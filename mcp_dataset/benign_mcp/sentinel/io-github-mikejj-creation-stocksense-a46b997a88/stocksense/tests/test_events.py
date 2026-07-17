"""Tests for key events tool."""

import pytest

from stocksense.data.market import fetch_key_events
from stocksense.tools.events import get_key_events


class TestFetchKeyEvents:
    def test_returns_valid_data(self):
        result = fetch_key_events("AAPL")
        assert result["ticker"] == "AAPL"
        assert "upcoming_earnings" in result
        assert "earnings_estimate" in result

    def test_earnings_estimate_structure(self):
        result = fetch_key_events("MSFT")
        est = result["earnings_estimate"]
        assert "eps_average" in est
        assert "revenue_average" in est

    def test_invalid_ticker(self):
        with pytest.raises((ValueError, RuntimeError)):
            fetch_key_events("INVALIDTICKER999XYZ")


class TestGetKeyEventsTool:
    def test_output_format(self):
        result = get_key_events("AAPL")
        assert result["ticker"] == "AAPL"
        assert "upcoming_earnings" in result
