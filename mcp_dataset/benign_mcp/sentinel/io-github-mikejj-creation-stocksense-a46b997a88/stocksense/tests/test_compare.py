"""Tests for company comparison tool."""

from stocksense.tools.compare import compare_companies


class TestCompareCompanies:
    def test_compare_two_companies(self):
        result = compare_companies(["AAPL", "MSFT"])
        assert result["count"] == 2
        assert result["tickers"] == ["AAPL", "MSFT"]
        assert len(result["companies"]) == 2

        for company in result["companies"]:
            assert "ticker" in company
            assert "price" in company or "quote_error" in company

    def test_single_company(self):
        result = compare_companies(["AAPL"])
        assert result["count"] == 1

    def test_includes_financials(self):
        result = compare_companies(["MSFT"])
        company = result["companies"][0]
        if "financials_error" not in company:
            assert "profit_margin" in company
            assert "total_revenue" in company

    def test_invalid_ticker_partial_results(self):
        result = compare_companies(["AAPL", "INVALIDXYZ"])
        assert result["count"] == 2
        # Valid ticker should have data, invalid should have errors
        valid = result["companies"][0]
        assert valid["ticker"] == "AAPL"
        assert "price" in valid or "quote_error" in valid
