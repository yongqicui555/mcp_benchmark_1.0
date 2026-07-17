"""StockSense — MCP server entry point."""

from mcp.server.fastmcp import FastMCP

from stocksense.tools.analyze import analyze_company as _analyze_company
from stocksense.tools.company_profile import get_company_profile as _get_company_profile
from stocksense.tools.compare import compare_companies as _compare_companies
from stocksense.tools.dividends import get_dividends as _get_dividends
from stocksense.tools.earnings import get_earnings as _get_earnings
from stocksense.tools.events import get_key_events as _get_key_events
from stocksense.tools.financials import get_financials as _get_financials
from stocksense.tools.insider_trades import get_insider_trades as _get_insider_trades
from stocksense.tools.price_history import get_price_history, get_quote
from stocksense.tools.sec_filings import get_filing as _get_filing
from stocksense.tools.sec_filings import search_filings as _search_filings
from stocksense.tools.technicals import get_technicals as _get_technicals
from stocksense.tools.validation import (
    validate_interval,
    validate_limit,
    validate_period,
    validate_statement,
    validate_ticker,
)

mcp = FastMCP("stocksense")


@mcp.tool()
def price_history(ticker: str, period: str = "1mo", interval: str = "1d") -> dict:
    """Get historical price data for a stock ticker.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)
        period: Time period — 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max
        interval: Data interval — 1m, 5m, 15m, 1h, 1d, 1wk, 1mo
    """
    ticker = validate_ticker(ticker)
    period = validate_period(period)
    interval = validate_interval(interval)
    return get_price_history(ticker, period, interval)


@mcp.tool()
def quote(ticker: str) -> dict:
    """Get current price quote and key stats for a stock ticker.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)
    """
    ticker = validate_ticker(ticker)
    return get_quote(ticker)


@mcp.tool()
def search_filings(ticker: str, form_type: str = "10-K", limit: int = 10) -> dict:
    """Search SEC EDGAR filings for a company.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)
        form_type: SEC form type — 10-K (annual), 10-Q (quarterly), 8-K (current events)
        limit: Maximum number of filings to return (default 10)
    """
    ticker = validate_ticker(ticker)
    limit = validate_limit(limit)
    return _search_filings(ticker, form_type, limit)


@mcp.tool()
def get_filing(ticker: str, accession_number: str) -> dict:
    """Get the full text of a specific SEC filing.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)
        accession_number: SEC accession number from search_filings results (e.g. 0000320193-24-000123)
    """
    ticker = validate_ticker(ticker)
    return _get_filing(ticker, accession_number)


@mcp.tool()
def insider_trades(ticker: str, limit: int = 20) -> dict:
    """Get recent insider trades (buys and sells) for a company from SEC Form 4 filings.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)
        limit: Maximum number of Form 4 filings to parse (default 20)
    """
    ticker = validate_ticker(ticker)
    limit = validate_limit(limit, max_limit=50)
    return _get_insider_trades(ticker, limit)


@mcp.tool()
def financials(ticker: str, statement: str = "income") -> dict:
    """Get financial statements and key ratios for a company.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)
        statement: Statement type — income, balance_sheet, cash_flow, or all
    """
    ticker = validate_ticker(ticker)
    statement = validate_statement(statement)
    return _get_financials(ticker, statement)


@mcp.tool()
def analyze_company(ticker: str) -> dict:
    """Get a comprehensive research brief for a company.

    Aggregates price, financials, insider trades, SEC filings, and analyst data.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)
    """
    ticker = validate_ticker(ticker)
    return _analyze_company(ticker)


@mcp.tool()
def compare_companies(tickers: list[str]) -> dict:
    """Compare key metrics across multiple companies side-by-side.

    Args:
        tickers: List of stock ticker symbols (e.g. ["AAPL", "MSFT", "GOOGL"])
    """
    if not tickers:
        raise ValueError("Must provide at least one ticker")
    if len(tickers) > 10:
        raise ValueError("Cannot compare more than 10 companies at once")
    validated = [validate_ticker(t) for t in tickers]
    return _compare_companies(validated)


@mcp.tool()
def earnings(ticker: str) -> dict:
    """Get quarterly earnings history with EPS estimates vs actuals and surprise percentages.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)
    """
    ticker = validate_ticker(ticker)
    return _get_earnings(ticker)


@mcp.tool()
def company_profile(ticker: str) -> dict:
    """Get company profile: sector, industry, employee count, and business description.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)
    """
    ticker = validate_ticker(ticker)
    return _get_company_profile(ticker)


@mcp.tool()
def dividends(ticker: str) -> dict:
    """Get dividend history and current yield for a company.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)
    """
    ticker = validate_ticker(ticker)
    return _get_dividends(ticker)


@mcp.tool()
def key_events(ticker: str) -> dict:
    """Get upcoming key dates: earnings dates, ex-dividend date, and EPS/revenue estimates.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)
    """
    ticker = validate_ticker(ticker)
    return _get_key_events(ticker)


@mcp.tool()
def technicals(ticker: str) -> dict:
    """Get technical indicators: moving averages (SMA/EMA), RSI, MACD, and performance stats.

    Args:
        ticker: Stock ticker symbol (e.g. AAPL, MSFT, GOOGL)
    """
    ticker = validate_ticker(ticker)
    return _get_technicals(ticker)


def main():
    """Run the MCP server on stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
