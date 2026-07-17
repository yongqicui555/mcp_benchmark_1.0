"""MCP tool definitions for insider trades."""

from stocksense.data.edgar import fetch_insider_trades


def get_insider_trades(ticker: str, limit: int = 20) -> dict:
    """Get recent insider trades for a company.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)
        limit: Maximum number of Form 4 filings to parse (default 20)

    Returns:
        Dict with ticker and list of insider transactions (buys and sells).
    """
    trades = fetch_insider_trades(ticker, limit)
    return {
        "ticker": ticker.upper(),
        "trade_count": len(trades),
        "trades": trades,
    }
