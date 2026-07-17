"""Input validation for MCP tools."""

import re

VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"}
VALID_INTERVALS = {"1m", "5m", "15m", "1h", "1d", "1wk", "1mo"}
VALID_STATEMENTS = {"income", "balance_sheet", "cash_flow", "all"}
VALID_FORM_TYPES = {"10-K", "10-Q", "8-K", "4", "SC 13G", "SC 13D", "DEF 14A", "S-1"}

_TICKER_RE = re.compile(r"^[A-Za-z]{1,5}([.-][A-Za-z]{1,2})?$")


def validate_ticker(ticker: str) -> str:
    """Validate and normalize a ticker symbol. Returns uppercase ticker."""
    ticker = ticker.strip()
    if not ticker:
        raise ValueError("Ticker symbol cannot be empty")
    if not _TICKER_RE.match(ticker):
        raise ValueError(
            f"Invalid ticker format '{ticker}'. "
            "Expected 1-5 letters, optionally followed by .X or -X (e.g. AAPL, BRK-B)"
        )
    return ticker.upper()


def validate_period(period: str) -> str:
    """Validate a price history period."""
    if period not in VALID_PERIODS:
        raise ValueError(f"Invalid period '{period}'. Valid options: {', '.join(sorted(VALID_PERIODS))}")
    return period


def validate_interval(interval: str) -> str:
    """Validate a price history interval."""
    if interval not in VALID_INTERVALS:
        raise ValueError(f"Invalid interval '{interval}'. Valid options: {', '.join(sorted(VALID_INTERVALS))}")
    return interval


def validate_statement(statement: str) -> str:
    """Validate a financial statement type."""
    if statement not in VALID_STATEMENTS:
        raise ValueError(f"Invalid statement type '{statement}'. Valid options: {', '.join(sorted(VALID_STATEMENTS))}")
    return statement


def validate_limit(limit: int, max_limit: int = 100) -> int:
    """Validate a limit parameter."""
    if limit < 1:
        raise ValueError("Limit must be at least 1")
    if limit > max_limit:
        raise ValueError(f"Limit cannot exceed {max_limit}")
    return limit
