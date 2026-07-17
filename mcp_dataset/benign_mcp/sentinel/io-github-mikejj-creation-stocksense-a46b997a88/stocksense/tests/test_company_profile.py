"""Tests for company profile tool."""

import pytest

from stocksense.data.market import fetch_sector_info
from stocksense.tools.company_profile import get_company_profile


class TestFetchSectorInfo:
    def test_returns_valid_data(self):
        result = fetch_sector_info("AAPL")
        assert result["ticker"] == "AAPL"
        assert result["sector"] is not None
        assert result["industry"] is not None

    def test_includes_summary(self):
        result = fetch_sector_info("MSFT")
        assert result["summary"] is not None
        assert len(result["summary"]) > 50

    def test_invalid_ticker(self):
        with pytest.raises((ValueError, RuntimeError)):
            fetch_sector_info("INVALIDTICKER999XYZ")


class TestGetCompanyProfileTool:
    def test_output_format(self):
        result = get_company_profile("AAPL")
        assert result["ticker"] == "AAPL"
        assert "sector" in result
        assert "industry" in result
        assert "country" in result
