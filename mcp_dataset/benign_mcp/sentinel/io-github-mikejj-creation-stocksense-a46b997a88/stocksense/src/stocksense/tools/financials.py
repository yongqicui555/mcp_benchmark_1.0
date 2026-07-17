"""MCP tool definitions for financial statements."""

from stocksense.data.market import fetch_financials


def get_financials(ticker: str, statement: str = "income") -> dict:
    """Get financial statements and key ratios for a company.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)
        statement: Statement type — income, balance_sheet, cash_flow, or all

    Returns:
        Dict with financial statement data and key ratios.
    """
    return fetch_financials(ticker, statement)
