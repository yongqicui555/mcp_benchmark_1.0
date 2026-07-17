"""MCP tool definitions for price history."""

from stocksense.data.market import fetch_price_history, fetch_quote


def get_price_history(ticker: str, period: str = "1mo", interval: str = "1d") -> dict:
    """Get historical price data for a stock ticker.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)
        period: Time period — 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max
        interval: Data interval — 1m, 5m, 15m, 1h, 1d, 1wk, 1mo

    Returns:
        Dict with ticker, period, interval, and list of OHLCV price bars.
    """
    data = fetch_price_history(ticker, period, interval)
    return {
        "ticker": ticker.upper(),
        "period": period,
        "interval": interval,
        "data_points": len(data),
        "data": data,
    }


def get_quote(ticker: str) -> dict:
    """Get current price quote and key stats for a stock ticker.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)

    Returns:
        Dict with current price, market cap, P/E ratio, 52-week range, and volume.
    """
    return fetch_quote(ticker)
