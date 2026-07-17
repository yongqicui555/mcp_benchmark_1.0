"""MCP tool definitions for SEC filings."""

from stocksense.data.edgar import fetch_filing_document, fetch_filings


def search_filings(
    ticker: str,
    form_type: str = "10-K",
    limit: int = 10,
) -> dict:
    """Search SEC EDGAR filings for a company.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)
        form_type: SEC form type — 10-K, 10-Q, 8-K, etc.
        limit: Maximum number of filings to return (default 10)

    Returns:
        Dict with ticker, form_type, and list of filing metadata.
    """
    filings = fetch_filings(ticker, form_type, limit)
    return {
        "ticker": ticker.upper(),
        "form_type": form_type,
        "count": len(filings),
        "filings": filings,
    }


def get_filing(ticker: str, accession_number: str) -> dict:
    """Get the full text of a specific SEC filing.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)
        accession_number: SEC accession number (e.g. 0000320193-24-000123)

    Returns:
        Dict with ticker, accession_number, and document text.
    """
    text = fetch_filing_document(ticker, accession_number)
    return {
        "ticker": ticker.upper(),
        "accession_number": accession_number,
        "document": text,
    }
