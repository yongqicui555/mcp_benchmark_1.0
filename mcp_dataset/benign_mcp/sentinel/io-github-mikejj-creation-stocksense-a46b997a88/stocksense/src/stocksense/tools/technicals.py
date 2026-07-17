"""MCP tool definitions for technical indicators."""

from stocksense.data.technicals import compute_technicals


def get_technicals(ticker: str) -> dict:
    """Get technical indicators and signals for a stock.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)

    Returns:
        Dict with moving averages (SMA/EMA), RSI, MACD, signals, and performance.
    """
    return compute_technicals(ticker)
