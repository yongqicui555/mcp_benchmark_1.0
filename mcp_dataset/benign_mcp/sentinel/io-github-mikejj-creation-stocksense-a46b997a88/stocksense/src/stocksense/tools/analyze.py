"""MCP tool definitions for company analysis."""

from stocksense.data.edgar import fetch_filings, fetch_insider_trades
from stocksense.data.market import (
    fetch_analyst_info,
    fetch_earnings_history,
    fetch_financials,
    fetch_quote,
    fetch_sector_info,
)


def analyze_company(ticker: str) -> dict:
    """Generate a structured research brief for a company.

    Aggregates data from all available sources into a single dict
    optimized for LLM analysis.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)

    Returns:
        Dict with quote, financials, insider activity, filings, and analyst data.
    """
    ticker_upper = ticker.upper()
    brief: dict = {"ticker": ticker_upper}

    # Quote and price context
    try:
        q = fetch_quote(ticker)
        brief["quote"] = q
        if q.get("price") and q.get("fifty_two_week_high") and q.get("fifty_two_week_low"):
            high = q["fifty_two_week_high"]
            low = q["fifty_two_week_low"]
            price = q["price"]
            brief["price_context"] = {
                "pct_from_52w_high": round((price - high) / high * 100, 1),
                "pct_from_52w_low": round((price - low) / low * 100, 1),
                "position_in_range": round((price - low) / (high - low) * 100, 1) if high != low else 50.0,
            }
    except Exception:
        brief["quote"] = {"error": "Failed to fetch quote data"}

    # Key financials
    try:
        fin = fetch_financials(ticker, "all")
        brief["financials"] = {
            "ratios": fin.get("ratios", {}),
        }
        # Extract latest period revenue and net income from income statement
        income = fin.get("income_statement", [])
        if income:
            latest = income[0]
            brief["financials"]["latest_period"] = latest.get("period")
            brief["financials"]["total_revenue"] = latest.get("Total Revenue")
            brief["financials"]["net_income"] = latest.get("Net Income")
            brief["financials"]["gross_profit"] = latest.get("Gross Profit")
            brief["financials"]["operating_income"] = latest.get("Operating Income")
    except Exception:
        brief["financials"] = {"error": "Failed to fetch financial data"}

    # Insider trading summary
    try:
        trades = fetch_insider_trades(ticker, limit=20)
        buys = [t for t in trades if t["transaction_type"] == "buy"]
        sells = [t for t in trades if t["transaction_type"] == "sell"]
        brief["insider_activity"] = {
            "total_transactions": len(trades),
            "buys": len(buys),
            "sells": len(sells),
            "net_buy_value": round(
                sum(t["value"] for t in buys) - sum(t["value"] for t in sells), 2
            ),
            "recent_trades": trades[:5],
        }
    except Exception:
        brief["insider_activity"] = {"error": "Failed to fetch insider data"}

    # Recent filings
    try:
        filings_10k = fetch_filings(ticker, "10-K", limit=3)
        filings_10q = fetch_filings(ticker, "10-Q", limit=3)
        brief["recent_filings"] = {
            "latest_10k": filings_10k[:1],
            "latest_10q": filings_10q[:1],
            "recent_10k_dates": [f["filing_date"] for f in filings_10k],
            "recent_10q_dates": [f["filing_date"] for f in filings_10q],
        }
    except Exception:
        brief["recent_filings"] = {"error": "Failed to fetch filing data"}

    # Analyst consensus
    try:
        analyst = fetch_analyst_info(ticker)
        brief["analyst_consensus"] = analyst
    except Exception:
        brief["analyst_consensus"] = {"error": "Failed to fetch analyst data"}

    # Earnings history
    try:
        earnings = fetch_earnings_history(ticker)
        brief["earnings"] = {
            "trailing_eps": earnings.get("trailing_eps"),
            "forward_eps": earnings.get("forward_eps"),
            "earnings_growth": earnings.get("earnings_growth"),
            "recent_quarters": earnings.get("quarters", [])[:4],
        }
    except Exception:
        brief["earnings"] = {"error": "Failed to fetch earnings data"}

    # Company profile
    try:
        profile = fetch_sector_info(ticker)
        brief["profile"] = {
            "sector": profile.get("sector"),
            "industry": profile.get("industry"),
            "employees": profile.get("full_time_employees"),
            "country": profile.get("country"),
        }
    except Exception:
        brief["profile"] = {"error": "Failed to fetch profile data"}

    return brief
