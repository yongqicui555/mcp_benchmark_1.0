"""yfinance wrapper for market data fetching."""

import yfinance as yf

from stocksense.data.cache import financials_cache, price_cache, quote_cache


def fetch_price_history(
    ticker: str,
    period: str = "1mo",
    interval: str = "1d",
) -> list[dict]:
    """Fetch historical price data for a ticker.

    Returns list of dicts with keys: date, open, high, low, close, volume.
    """
    cache_key = f"price:{ticker}:{period}:{interval}"
    cached = price_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        df = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
        )
    except Exception as e:
        raise RuntimeError(f"Failed to fetch price data for {ticker}: {e}") from e

    if df.empty:
        raise ValueError(f"No price data returned for ticker '{ticker}'")

    # yf.download returns MultiIndex columns when single ticker; flatten
    if hasattr(df.columns, "droplevel") and df.columns.nlevels > 1:
        df.columns = df.columns.droplevel(1)

    records: list[dict] = []
    for idx, row in df.iterrows():
        records.append(
            {
                "date": idx.strftime("%Y-%m-%d") if interval in ("1d", "1wk", "1mo") else idx.isoformat(),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            }
        )

    price_cache.set(cache_key, records)
    return records


def fetch_quote(ticker: str) -> dict:
    """Fetch current quote snapshot for a ticker."""
    cache_key = f"quote:{ticker}"
    cached = quote_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        info = yf.Ticker(ticker).info
    except Exception as e:
        raise RuntimeError(f"Failed to fetch quote for {ticker}: {e}") from e

    if not info or info.get("regularMarketPrice") is None:
        raise ValueError(f"No quote data available for ticker '{ticker}'")

    quote = {
        "ticker": ticker.upper(),
        "price": info.get("regularMarketPrice"),
        "previous_close": info.get("previousClose"),
        "open": info.get("regularMarketOpen"),
        "day_high": info.get("dayHigh"),
        "day_low": info.get("dayLow"),
        "volume": info.get("volume"),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
        "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
        "name": info.get("shortName"),
    }

    quote_cache.set(cache_key, quote)
    return quote


def _df_to_records(df, label: str) -> list[dict]:
    """Convert a yfinance financial DataFrame to list of dicts with period keys."""
    if df is None or df.empty:
        return []
    records = []
    for col in df.columns:
        period_label = col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)
        row_data = {}
        for idx, val in df[col].items():
            if val is not None and not (isinstance(val, float) and __import__("math").isnan(val)):
                row_data[str(idx)] = round(float(val), 2) if isinstance(val, (int, float)) else val
        records.append({"period": period_label, **row_data})
    return records


def fetch_financials(ticker: str, statement: str = "income") -> dict:
    """Fetch financial statements for a ticker.

    Args:
        statement: "income", "balance_sheet", "cash_flow", or "all"

    Returns dict with statement data as list of dicts per period.
    """
    cache_key = f"financials:{ticker}:{statement}"
    cached = financials_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
    except Exception as e:
        raise RuntimeError(f"Failed to fetch financials for {ticker}: {e}") from e

    if not info.get("shortName"):
        raise ValueError(f"No financial data available for ticker '{ticker}'")

    result = {"ticker": ticker.upper(), "name": info.get("shortName")}

    statements = {
        "income": ("income_statement", t.financials),
        "balance_sheet": ("balance_sheet", t.balance_sheet),
        "cash_flow": ("cash_flow", t.cashflow),
    }

    if statement == "all":
        for key, (label, df) in statements.items():
            result[label] = _df_to_records(df, label)
    elif statement in statements:
        label, df = statements[statement]
        result[label] = _df_to_records(df, label)
    else:
        raise ValueError(f"Unknown statement type '{statement}'. Use: income, balance_sheet, cash_flow, all")

    # Add key ratios from info
    result["ratios"] = {
        "profit_margin": info.get("profitMargins"),
        "operating_margin": info.get("operatingMargins"),
        "return_on_equity": info.get("returnOnEquity"),
        "return_on_assets": info.get("returnOnAssets"),
        "debt_to_equity": info.get("debtToEquity"),
        "current_ratio": info.get("currentRatio"),
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth": info.get("earningsGrowth"),
    }

    financials_cache.set(cache_key, result)
    return result


def fetch_analyst_info(ticker: str) -> dict:
    """Fetch analyst recommendations and target prices."""
    cache_key = f"analyst:{ticker}"
    cached = financials_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
    except Exception as e:
        raise RuntimeError(f"Failed to fetch analyst info for {ticker}: {e}") from e

    result = {
        "ticker": ticker.upper(),
        "recommendation": info.get("recommendationKey"),
        "target_mean_price": info.get("targetMeanPrice"),
        "target_high_price": info.get("targetHighPrice"),
        "target_low_price": info.get("targetLowPrice"),
        "number_of_analysts": info.get("numberOfAnalystOpinions"),
    }

    financials_cache.set(cache_key, result)
    return result


def fetch_dividends(ticker: str) -> dict:
    """Fetch dividend history and current yield for a ticker."""
    cache_key = f"dividends:{ticker}"
    cached = financials_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        divs = t.dividends
    except Exception as e:
        raise RuntimeError(f"Failed to fetch dividends for {ticker}: {e}") from e

    if not info.get("shortName"):
        raise ValueError(f"No dividend data available for ticker '{ticker}'")

    history = []
    if divs is not None and not divs.empty:
        for date_idx, amount in divs.items():
            history.append({
                "date": date_idx.strftime("%Y-%m-%d"),
                "amount": round(float(amount), 4),
            })

    result = {
        "ticker": ticker.upper(),
        "name": info.get("shortName"),
        "dividend_rate": info.get("dividendRate"),
        "dividend_yield": info.get("dividendYield"),
        "payout_ratio": info.get("payoutRatio"),
        "five_year_avg_yield": info.get("fiveYearAvgDividendYield"),
        "ex_dividend_date": info.get("exDividendDate"),
        "history": history[-20:],  # Last 20 dividends
    }

    financials_cache.set(cache_key, result)
    return result


def fetch_key_events(ticker: str) -> dict:
    """Fetch upcoming key dates and events for a ticker."""
    cache_key = f"events:{ticker}"
    cached = financials_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        cal = t.calendar or {}
    except Exception as e:
        raise RuntimeError(f"Failed to fetch events for {ticker}: {e}") from e

    if not info.get("shortName"):
        raise ValueError(f"No event data available for ticker '{ticker}'")

    earnings_dates = cal.get("Earnings Date", [])
    earnings_date_strs = []
    for d in (earnings_dates if isinstance(earnings_dates, list) else [earnings_dates]):
        if d is not None:
            earnings_date_strs.append(d.isoformat() if hasattr(d, "isoformat") else str(d))

    ex_div = cal.get("Ex-Dividend Date")
    div_date = cal.get("Dividend Date")

    result = {
        "ticker": ticker.upper(),
        "name": info.get("shortName"),
        "upcoming_earnings": earnings_date_strs,
        "earnings_estimate": {
            "eps_average": cal.get("Earnings Average"),
            "eps_high": cal.get("Earnings High"),
            "eps_low": cal.get("Earnings Low"),
            "revenue_average": cal.get("Revenue Average"),
        },
        "ex_dividend_date": ex_div.isoformat() if hasattr(ex_div, "isoformat") else None,
        "dividend_date": div_date.isoformat() if hasattr(div_date, "isoformat") else None,
    }

    financials_cache.set(cache_key, result)
    return result


def fetch_earnings_history(ticker: str) -> dict:
    """Fetch quarterly earnings history (EPS estimates vs actuals)."""
    cache_key = f"earnings:{ticker}"
    cached = financials_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        eh = t.earnings_history
    except Exception as e:
        raise RuntimeError(f"Failed to fetch earnings for {ticker}: {e}") from e

    if not info.get("shortName"):
        raise ValueError(f"No earnings data available for ticker '{ticker}'")

    quarters = []
    if eh is not None and not eh.empty:
        for idx, row in eh.iterrows():
            quarter_label = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)
            quarters.append({
                "quarter": quarter_label,
                "eps_actual": round(float(row.get("epsActual", 0)), 2),
                "eps_estimate": round(float(row.get("epsEstimate", 0)), 2),
                "eps_difference": round(float(row.get("epsDifference", 0)), 2),
                "surprise_pct": round(float(row.get("surprisePercent", 0)) * 100, 1),
            })

    result = {
        "ticker": ticker.upper(),
        "name": info.get("shortName"),
        "trailing_eps": info.get("trailingEps"),
        "forward_eps": info.get("forwardEps"),
        "earnings_growth": info.get("earningsGrowth"),
        "quarters": quarters,
    }

    financials_cache.set(cache_key, result)
    return result


def fetch_sector_info(ticker: str) -> dict:
    """Fetch sector, industry, and company profile for a ticker."""
    cache_key = f"sector:{ticker}"
    cached = financials_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        info = yf.Ticker(ticker).info or {}
    except Exception as e:
        raise RuntimeError(f"Failed to fetch sector info for {ticker}: {e}") from e

    if not info.get("shortName"):
        raise ValueError(f"No sector data available for ticker '{ticker}'")

    result = {
        "ticker": ticker.upper(),
        "name": info.get("shortName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "full_time_employees": info.get("fullTimeEmployees"),
        "country": info.get("country"),
        "website": info.get("website"),
        "summary": info.get("longBusinessSummary"),
    }

    financials_cache.set(cache_key, result)
    return result
