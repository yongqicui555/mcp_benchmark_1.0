"""Tests for insider trades tool output format."""

from stocksense.tools.insider_trades import get_insider_trades


class TestGetInsiderTrades:
    def test_output_format(self):
        result = get_insider_trades("AAPL", limit=5)
        assert result["ticker"] == "AAPL"
        assert "trade_count" in result
        assert result["trade_count"] == len(result["trades"])
        assert isinstance(result["trades"], list)

    def test_trade_fields(self):
        result = get_insider_trades("AAPL", limit=10)
        if result["trade_count"] > 0:
            t = result["trades"][0]
            expected_keys = {
                "filing_date", "transaction_date", "insider_name",
                "title", "relationship", "transaction_type",
                "shares", "price_per_share", "value",
            }
            assert expected_keys.issubset(set(t.keys()))
