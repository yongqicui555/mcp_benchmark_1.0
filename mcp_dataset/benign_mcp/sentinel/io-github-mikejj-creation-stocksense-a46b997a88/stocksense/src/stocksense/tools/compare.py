"""MCP tool definitions for comparing multiple companies."""

from stocksense.data.market import fetch_financials, fetch_quote


def compare_companies(tickers: list[str]) -> dict:
    """Compare key metrics across multiple companies side-by-side.

    Args:
        tickers: List of stock ticker symbols (e.g. ["AAPL", "MSFT", "GOOGL"])

    Returns:
        Dict with comparison table of key metrics per company.
    """
    comparisons = []

    for ticker in tickers:
        entry = {"ticker": ticker.upper()}

        try:
            q = fetch_quote(ticker)
            entry["price"] = q.get("price")
            entry["market_cap"] = q.get("market_cap")
            entry["pe_ratio"] = q.get("pe_ratio")
            entry["fifty_two_week_high"] = q.get("fifty_two_week_high")
            entry["fifty_two_week_low"] = q.get("fifty_two_week_low")
            entry["name"] = q.get("name")
        except Exception:
            entry["quote_error"] = "Failed to fetch quote"

        try:
            fin = fetch_financials(ticker, "income")
            ratios = fin.get("ratios", {})
            entry["profit_margin"] = ratios.get("profit_margin")
            entry["revenue_growth"] = ratios.get("revenue_growth")
            entry["return_on_equity"] = ratios.get("return_on_equity")
            entry["debt_to_equity"] = ratios.get("debt_to_equity")

            income = fin.get("income_statement", [])
            if income:
                latest = income[0]
                entry["total_revenue"] = latest.get("Total Revenue")
                entry["net_income"] = latest.get("Net Income")
        except Exception:
            entry["financials_error"] = "Failed to fetch financials"

        comparisons.append(entry)

    return {
        "tickers": [t.upper() for t in tickers],
        "count": len(comparisons),
        "companies": comparisons,
    }
