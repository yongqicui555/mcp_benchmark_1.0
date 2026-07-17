"""MCP tool definitions for company profile."""

from stocksense.data.market import fetch_sector_info


def get_company_profile(ticker: str) -> dict:
    """Get company profile including sector, industry, and business description.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)

    Returns:
        Dict with sector, industry, employee count, country, and business summary.
    """
    return fetch_sector_info(ticker)
