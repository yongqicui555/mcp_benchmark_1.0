# StockSense

<!-- mcp-name: io.github.mikejj-creation/stocksense -->

[![PyPI version](https://img.shields.io/pypi/v/stocksense)](https://pypi.org/project/stocksense/)
[![PyPI downloads](https://img.shields.io/pypi/dm/stocksense)](https://pypi.org/project/stocksense/)
[![Python versions](https://img.shields.io/pypi/pyversions/stocksense)](https://pypi.org/project/stocksense/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

An MCP (Model Context Protocol) server that gives AI agents access to financial data — SEC EDGAR filings, market fundamentals, insider trades, and price history. No API keys needed.

## Quick Start

### 1. Install

```bash
pip install stocksense
```

### 2. Add to Claude Desktop

Add to your Claude Desktop config:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "stocksense": {
      "command": "stocksense"
    }
  }
}
```

### 3. Restart Claude Desktop

Quit and reopen Claude Desktop. You should see the hammer icon with 13 tools available.

### Available Tools

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

### Example queries

- "What's AAPL's price history for the last month?"
- "Get me a quote for MSFT"
- "Show me TSLA's weekly prices over the past year"
- "Show me Apple's recent 10-K filings"
- "What insider trades happened at Tesla recently?"
- "Show me Apple's financial statements"
- "Give me a research brief on Tesla"
- "Compare AAPL, MSFT, and GOOGL"
- "Show me Apple's earnings history"
- "What sector is NVIDIA in?"
- "Show me AAPL's dividend history"
- "When is Microsoft's next earnings date?"
- "What are Tesla's technical indicators?"

## Data Sources

- **yfinance** — price data, quotes, financial statements, analyst consensus
- **SEC EDGAR** — free, unlimited filings and insider trades (no API key needed)

## Requirements

- Python 3.11+
- No API keys needed — uses free public data sources

## Development

```bash
# Clone and install for development
git clone https://github.com/mikejj-creation/stocksense.git
cd stocksense
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check src/ tests/
```

## Disclaimer

StockSense uses free public data from Yahoo Finance and SEC EDGAR. Users are responsible for complying with each provider's terms of service. This tool is for informational purposes only — not financial advice.

## License

MIT
