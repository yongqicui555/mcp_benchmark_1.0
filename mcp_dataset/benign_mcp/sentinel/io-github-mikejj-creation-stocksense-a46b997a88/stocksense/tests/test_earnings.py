"""Tests for earnings history tool."""

import pytest

from stocksense.data.market import fetch_earnings_history
from stocksense.tools.earnings import get_earnings


class TestFetchEarningsHistory:
    def test_returns_valid_data(self):
        result = fetch_earnings_history("AAPL")
        assert result["ticker"] == "AAPL"
        assert "trailing_eps" in result
        assert "forward_eps" in result
        assert "quarters" in result

    def test_quarters_structure(self):
        result = fetch_earnings_history("MSFT")
        if result["quarters"]:
            q = result["quarters"][0]
            assert "quarter" in q
            assert "eps_actual" in q
            assert "eps_estimate" in q
            assert "surprise_pct" in q

    def test_invalid_ticker(self):
        with pytest.raises((ValueError, RuntimeError)):
            fetch_earnings_history("INVALIDTICKER999XYZ")


class TestGetEarningsTool:
    def test_output_format(self):
        result = get_earnings("AAPL")
        assert result["ticker"] == "AAPL"
        assert "quarters" in result
