"""Integration tests for SEC EDGAR data layer."""

import pytest

from stocksense.data.edgar import (
    _resolve_cik,
    fetch_filing_document,
    fetch_filings,
    fetch_insider_trades,
)


class TestCIKMapping:
    def test_known_ticker(self):
        cik = _resolve_cik("AAPL")
        assert cik is not None
        assert len(cik) == 10
        assert cik.isdigit()

    def test_invalid_ticker(self):
        with pytest.raises(ValueError, match="not found"):
            _resolve_cik("INVALIDTICKER999XYZ")

    def test_case_insensitive(self):
        assert _resolve_cik("aapl") == _resolve_cik("AAPL")


class TestFetchFilings:
    def test_returns_10k_filings(self):
        filings = fetch_filings("AAPL", "10-K", limit=3)
        assert len(filings) > 0
        first = filings[0]
        assert "filing_date" in first
        assert "accession_number" in first
        assert first["form_type"] == "10-K"

    def test_returns_8k_filings(self):
        filings = fetch_filings("AAPL", "8-K", limit=3)
        assert len(filings) > 0
        assert filings[0]["form_type"] == "8-K"

    def test_respects_limit(self):
        filings = fetch_filings("AAPL", "10-Q", limit=2)
        assert len(filings) <= 2

    def test_invalid_ticker(self):
        with pytest.raises(ValueError):
            fetch_filings("INVALIDTICKER999XYZ")


class TestFetchFilingDocument:
    def test_fetches_document(self):
        # First get a real accession number
        filings = fetch_filings("MSFT", "10-K", limit=1)
        assert len(filings) > 0
        acc = filings[0]["accession_number"]

        text = fetch_filing_document("MSFT", acc)
        assert len(text) > 100
        assert isinstance(text, str)

    def test_invalid_accession(self):
        with pytest.raises(ValueError, match="not found"):
            fetch_filing_document("AAPL", "0000000000-00-000000")


class TestFetchInsiderTrades:
    def test_returns_trades(self):
        trades = fetch_insider_trades("AAPL", limit=5)
        # AAPL may or may not have recent Form 4s, but the call should succeed
        assert isinstance(trades, list)

    def test_trade_structure(self):
        trades = fetch_insider_trades("AAPL", limit=10)
        if len(trades) > 0:
            t = trades[0]
            assert "insider_name" in t
            assert "transaction_type" in t
            assert t["transaction_type"] in ("buy", "sell")
            assert "shares" in t
            assert "price_per_share" in t
            assert "value" in t

    def test_invalid_ticker(self):
        with pytest.raises(ValueError):
            fetch_insider_trades("INVALIDTICKER999XYZ")
