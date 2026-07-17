# StockSense

MCP server giving AI agents access to financial data — SEC EDGAR filings, market fundamentals, insider trades, price history, technicals, and more. No API keys needed.

- **Version:** 0.1.1
- **License:** MIT
- **Language:** Python
- **Runtime:** Python >= 3.11

## Category

Finance

## Tags

finance, stocks, sec, edgar, mcp, ai, llm, market-data, insider-trades, price-history, fundamentals, earnings, dividends, technicals

## Use Cases

- **Stock Research:** Get historical prices, quotes, financial statements, and earnings data for any public company
- **SEC Filing Analysis:** Search and read 10-K, 10-Q, 8-K filings directly from SEC EDGAR
- **Insider Trade Monitoring:** Track recent insider buys and sells from Form 4 filings
- **Company Comparison:** Compare key metrics across multiple companies side-by-side
- **Technical Analysis:** View SMA, EMA, RSI, MACD, and performance indicators

## Tools

| Tool | Description |
|------|-------------|
| `price_history` | Get historical OHLCV price data for any ticker |
| `quote` | Get current price, market cap, P/E, 52-week range |
| `search_filings` | Search SEC EDGAR filings (10-K, 10-Q, 8-K) |
| `get_filing` | Get full text of a specific SEC filing |
| `insider_trades` | Get recent insider buys/sells from Form 4 filings |
| `financials` | Get income statement, balance sheet, cash flow, and key ratios |
| `analyze_company` | Comprehensive research brief aggregating all data sources |
| `compare_companies` | Compare key metrics across multiple companies side-by-side |
| `earnings` | Quarterly earnings history with EPS estimates vs actuals |
| `company_profile` | Company profile: sector, industry, and business description |
| `dividends` | Dividend history and current yield |
| `key_events` | Upcoming earnings dates, ex-dividend date, and estimates |
| `technicals` | Technical indicators: SMA, EMA, RSI, MACD, and performance |

## Setup Requirements

- Python 3.11+
- No API keys needed — uses free public data sources (Yahoo Finance, SEC EDGAR)

## Installation

```bash
pip install stocksense
```

### Claude Desktop Configuration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "stocksense": {
      "command": "stocksense"
    }
  }
}
```

## Pricing

Free and open source (MIT)

## Links

- Repository: https://github.com/mikejj-creation/stocksense
- PyPI: https://pypi.org/project/stocksense/
- Issues: https://github.com/mikejj-creation/stocksense/issues
