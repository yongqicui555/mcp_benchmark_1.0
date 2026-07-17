"""MCP tool definitions for earnings data."""

from stocksense.data.market import fetch_earnings_history


def get_earnings(ticker: str) -> dict:
    """Get quarterly earnings history with EPS estimates vs actuals.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)

    Returns:
        Dict with trailing/forward EPS, growth rate, and quarterly earnings history.
    """
    return fetch_earnings_history(ticker)
