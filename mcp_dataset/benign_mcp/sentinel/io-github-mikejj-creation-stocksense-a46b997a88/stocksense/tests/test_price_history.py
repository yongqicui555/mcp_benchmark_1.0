"""Integration tests for price history tools."""

import pytest

from stocksense.data.market import fetch_price_history, fetch_quote
from stocksense.tools.price_history import get_price_history, get_quote


class TestFetchPriceHistory:
    def test_returns_valid_data(self):
        records = fetch_price_history("AAPL", "5d", "1d")
        assert len(records) > 0
        first = records[0]
        assert set(first.keys()) == {"date", "open", "high", "low", "close", "volume"}
        assert isinstance(first["open"], float)
        assert isinstance(first["volume"], int)

    def test_invalid_ticker(self):
        with pytest.raises((ValueError, RuntimeError)):
            fetch_price_history("INVALIDTICKER999XYZ", "5d", "1d")


class TestFetchQuote:
    def test_returns_valid_quote(self):
        q = fetch_quote("AAPL")
        assert q["ticker"] == "AAPL"
        assert q["price"] is not None
        assert isinstance(q["price"], (int, float))

    def test_invalid_ticker(self):
        with pytest.raises((ValueError, RuntimeError)):
            fetch_quote("INVALIDTICKER999XYZ")


class TestToolOutput:
    def test_get_price_history_format(self):
        result = get_price_history("MSFT", "5d", "1d")
        assert result["ticker"] == "MSFT"
        assert result["period"] == "5d"
        assert result["interval"] == "1d"
        assert result["data_points"] == len(result["data"])
        assert len(result["data"]) > 0

    def test_get_quote_format(self):
        result = get_quote("MSFT")
        assert result["ticker"] == "MSFT"
        assert "price" in result
        assert "market_cap" in result
