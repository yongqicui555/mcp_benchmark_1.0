"""Tests for company analysis tool."""


from stocksense.tools.analyze import analyze_company


class TestAnalyzeCompany:
    def test_returns_all_sections(self):
        result = analyze_company("AAPL")
        assert result["ticker"] == "AAPL"
        assert "quote" in result
        assert "financials" in result
        assert "insider_activity" in result
        assert "recent_filings" in result
        assert "analyst_consensus" in result

    def test_price_context(self):
        result = analyze_company("MSFT")
        if "price_context" in result:
            ctx = result["price_context"]
            assert "pct_from_52w_high" in ctx
            assert "pct_from_52w_low" in ctx
            assert "position_in_range" in ctx

    def test_insider_summary(self):
        result = analyze_company("AAPL")
        insider = result["insider_activity"]
        if "error" not in insider:
            assert "buys" in insider
            assert "sells" in insider
            assert "net_buy_value" in insider

    def test_invalid_ticker_still_returns(self):
        # analyze_company catches errors per-section, so it should still return a dict
        result = analyze_company("INVALIDTICKER999XYZ")
        assert result["ticker"] == "INVALIDTICKER999XYZ"
        # At least some sections should have error messages
        has_errors = any(
            isinstance(result.get(k), dict) and "error" in result.get(k, {})
            for k in ["quote", "financials", "insider_activity", "recent_filings", "analyst_consensus"]
        )
        assert has_errors
