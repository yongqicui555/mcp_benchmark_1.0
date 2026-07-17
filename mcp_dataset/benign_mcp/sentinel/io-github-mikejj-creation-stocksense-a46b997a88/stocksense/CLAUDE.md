# CLAUDE.md

## Project Overview

StockSense — an open-source MCP server providing AI agents with access to financial data (SEC filings, fundamentals, insider trades, price history).

## Tech Stack

- Python 3.11+
- MCP SDK (`mcp` package)
- SEC EDGAR API (free, no key needed)
- yfinance (price data)
- Financial Modeling Prep or Alpha Vantage (fundamentals)

## Project Structure

```
stocksense/
├── src/
│   └── stocksense/
│       ├── __init__.py
│       ├── server.py          # MCP server entry point
│       ├── tools/             # Individual MCP tool implementations
│       │   ├── sec_filings.py
│       │   ├── financials.py
│       │   ├── insider_trades.py
│       │   ├── price_history.py
│       │   └── analyze.py
│       └── data/              # Data fetching and caching utilities
│           ├── edgar.py
│           ├── market.py
│           └── cache.py
├── tests/
├── pyproject.toml
├── README.md
└── CLAUDE.md
```

## Development Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the server
python -m stocksense

# Run tests
pytest
```

## Key Design Decisions

- All data sources are free or very cheap ($0-14/month)
- SEC EDGAR is the core differentiator (free, unlimited, rich data)
- Tools return structured data optimized for LLM consumption
- Caching layer to avoid redundant API calls
