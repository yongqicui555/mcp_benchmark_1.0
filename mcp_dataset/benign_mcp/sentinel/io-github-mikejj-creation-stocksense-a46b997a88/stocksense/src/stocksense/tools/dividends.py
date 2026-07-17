"""MCP tool definitions for dividend data."""

from stocksense.data.market import fetch_dividends


def get_dividends(ticker: str) -> dict:
    """Get dividend history and current yield for a company.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)

    Returns:
        Dict with dividend rate, yield, payout ratio, and payment history.
    """
    return fetch_dividends(ticker)
