"""Tests for SEC filings tool output format."""

from stocksense.tools.sec_filings import get_filing, search_filings


class TestSearchFilings:
    def test_output_format(self):
        result = search_filings("AAPL", "10-K", limit=3)
        assert result["ticker"] == "AAPL"
        assert result["form_type"] == "10-K"
        assert result["count"] == len(result["filings"])
        assert result["count"] > 0

    def test_8k_search(self):
        result = search_filings("MSFT", "8-K", limit=2)
        assert result["ticker"] == "MSFT"
        assert result["form_type"] == "8-K"


class TestGetFiling:
    def test_output_format(self):
        filings = search_filings("MSFT", "10-Q", limit=1)
        acc = filings["filings"][0]["accession_number"]
        result = get_filing("MSFT", acc)
        assert result["ticker"] == "MSFT"
        assert result["accession_number"] == acc
        assert len(result["document"]) > 100
