"""Tests for financial statements tool."""

import pytest

from stocksense.data.market import fetch_financials
from stocksense.tools.financials import get_financials


class TestFetchFinancials:
    def test_income_statement(self):
        result = fetch_financials("AAPL", "income")
        assert result["ticker"] == "AAPL"
        assert "income_statement" in result
        assert len(result["income_statement"]) > 0
        assert "period" in result["income_statement"][0]

    def test_balance_sheet(self):
        result = fetch_financials("AAPL", "balance_sheet")
        assert "balance_sheet" in result
        assert len(result["balance_sheet"]) > 0

    def test_cash_flow(self):
        result = fetch_financials("AAPL", "cash_flow")
        assert "cash_flow" in result
        assert len(result["cash_flow"]) > 0

    def test_all_statements(self):
        result = fetch_financials("MSFT", "all")
        assert "income_statement" in result
        assert "balance_sheet" in result
        assert "cash_flow" in result

    def test_ratios_included(self):
        result = fetch_financials("AAPL", "income")
        assert "ratios" in result
        ratios = result["ratios"]
        assert "profit_margin" in ratios
        assert "return_on_equity" in ratios
        assert "debt_to_equity" in ratios

    def test_invalid_ticker(self):
        with pytest.raises((ValueError, RuntimeError)):
            fetch_financials("INVALIDTICKER999XYZ")

    def test_invalid_statement_type(self):
        with pytest.raises(ValueError, match="Unknown statement type"):
            fetch_financials("AAPL", "nonsense")


class TestGetFinancialsTool:
    def test_output_format(self):
        result = get_financials("MSFT", "income")
        assert result["ticker"] == "MSFT"
        assert "income_statement" in result
        assert "ratios" in result
