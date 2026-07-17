"""MCP tool definitions for key company events."""

from stocksense.data.market import fetch_key_events


def get_key_events(ticker: str) -> dict:
    """Get upcoming key dates: earnings dates, ex-dividend date, and estimates.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)

    Returns:
        Dict with upcoming earnings dates, EPS/revenue estimates, and dividend dates.
    """
    return fetch_key_events(ticker)
