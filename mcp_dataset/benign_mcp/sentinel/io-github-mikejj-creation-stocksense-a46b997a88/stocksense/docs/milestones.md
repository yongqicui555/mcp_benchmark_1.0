# Milestones

---

## Milestone 1: Working MCP Server with Price History Tool

**Status: COMPLETE**

Delivered a functional MCP server that can be `pip install`-ed, connected to Claude Desktop, and queried for real price data — proving the end-to-end MCP plumbing works.

### Action Items

- [x] `src/stocksense/data/cache.py` — In-memory TTL cache with expiry timestamps
- [x] `src/stocksense/data/market.py` — yfinance wrapper with caching (`fetch_price_history`, `fetch_quote`)
- [x] `src/stocksense/tools/price_history.py` — Tool functions (`get_price_history`, `get_quote`)
- [x] `src/stocksense/server.py` — FastMCP server with stdio transport, registers price tools
- [x] `src/stocksense/__main__.py` — Module runner (`python -m stocksense`)
- [x] `tests/test_cache.py` — 6 unit tests for TTL cache
- [x] `tests/test_price_history.py` — 6 integration tests for price data + tool output format
- [x] `pyproject.toml` — Add `[project.scripts]` entry point
- [x] `README.md` — Installation, Claude Desktop config, usage docs

### Key Decisions

- **FastMCP** over low-level Server API — cleaner, decorator-based
- **Stdio transport** — standard for Claude Desktop / CLI
- **List of dicts** (not DataFrame) as internal format — easy JSON serialization
- **In-memory cache** (not file-based) — server is stateless, restarts are cheap

---

## Milestone 2: SEC EDGAR Filings & Insider Trades

**Status: COMPLETE**

Add two new tools backed by SEC EDGAR (free, unlimited API). These are the core differentiators — no API key needed, rich structured data. Reuse battle-tested patterns from `ai-investment-research-engine`.

### Context

SEC EDGAR provides:
- **Company filings** (10-K, 10-Q, 8-K) via `data.sec.gov/submissions/CIK{cik}.json`
- **Insider trades** (Form 4) via the same submissions endpoint + XML parsing
- Rate limit: 10 req/sec, requires descriptive User-Agent header
- CIK mapping from `sec.gov/files/company_tickers.json`

### Action Items

#### Data Layer

- [x] `src/stocksense/data/edgar.py` — SEC EDGAR client
  - [x] `_build_cik_map()` — Fetch and cache ticker→CIK mapping from `company_tickers.json`
  - [x] `_edgar_get(url)` — Shared request helper with User-Agent header, rate limiting (0.12s delay), 30s timeout, gzip decompression
  - [x] `fetch_filings(ticker, form_type, limit)` — Query submissions JSON, return filing metadata (date, accession, form type, items, primary doc)
  - [x] `fetch_filing_document(ticker, accession_number)` — Download and return primary filing document content
  - [x] `fetch_insider_trades(ticker, limit)` — Filter Form 4/4A filings, parse XML for transactions (insider name, title, relationship, buy/sell, shares, price, value)
  - [x] Integrate with TTL cache (filings: 30 min, CIK map: 24 hr)

#### Tools

- [x] `src/stocksense/tools/sec_filings.py` — MCP tool definitions
  - [x] `search_filings(ticker, form_type="10-K", limit=10)` — Search SEC filings, return metadata list
  - [x] `get_filing(ticker, accession_number)` — Fetch full filing document text (truncated for LLM context)
- [x] `src/stocksense/tools/insider_trades.py` — MCP tool definitions
  - [x] `get_insider_trades(ticker, limit=20)` — Return recent insider transactions with structured data

#### Server Registration

- [x] `src/stocksense/server.py` — Register new tools (`search_filings`, `get_filing`, `insider_trades`)

#### Tests

- [x] `tests/test_edgar.py` — Unit/integration tests (10 tests)
  - [x] Test CIK mapping lookup (AAPL → valid CIK)
  - [x] Test `fetch_filings` returns valid metadata for known ticker
  - [x] Test `fetch_insider_trades` returns structured transaction data
  - [x] Test invalid ticker handling
- [x] `tests/test_sec_filings.py` — Tool output format tests (3 tests)
- [x] `tests/test_insider_trades.py` — Tool output format tests (2 tests)

#### Docs

- [x] `README.md` — Add new tools to Available Tools table and example queries

### Key Decisions

- **No API key required** — SEC EDGAR is free and unlimited
- **User-Agent header** — Required by EDGAR policy; use project name + contact
- **Rate limiting at data layer** — 0.12s delay between requests (10 req/sec limit)
- **CIK map cached for 24 hours** — Changes infrequently, expensive to fetch
- **Filing text truncated** — Full 10-K can be 100k+ tokens; truncate to first N chars with a note
- **XML parsing with stdlib `xml.etree`** — No lxml dependency needed for Form 4 parsing
- **Accession number as filing ID** — Unique, stable, used in URLs

### EDGAR API Reference

| Endpoint | Purpose |
|----------|---------|
| `sec.gov/files/company_tickers.json` | Ticker → CIK mapping |
| `data.sec.gov/submissions/CIK{cik}.json` | Filing metadata (recent 100) |
| `sec.gov/Archives/edgar/data/{cik}/{accession}/{doc}` | Filing document |

### Verification

1. `pytest` — All new + existing tests pass
2. In Claude Desktop: "Show me Apple's recent 10-K filings"
3. In Claude Desktop: "What insider trades happened at Tesla recently?"
4. Existing price tools still work (no regressions)

---

## Milestone 3: Financial Statements & Company Analysis

**Status: COMPLETE**

Add the final two tools: `get_financials` for financial statements/ratios and `analyze_company` for an AI-friendly research summary. Both use free data sources only (yfinance + EDGAR) — no paid API keys needed.

### Context

The ai-investment-research-engine shows that yfinance provides:
- Income statement, balance sheet, cash flow via `Ticker.financials`, `Ticker.balance_sheet`, `Ticker.cashflow`
- Key ratios and stats via `Ticker.info`
- Analyst recommendations via `Ticker.recommendations`

For `analyze_company`, we aggregate data from all existing tools into a structured research brief the LLM can reason over — we don't call an LLM ourselves, we give the LLM the raw material to analyze.

### Action Items

#### Data Layer

- [x] `src/stocksense/data/market.py` — Add financial statement fetching
  - [x] `fetch_financials(ticker, statement)` — Income statement, balance sheet, cash flow from yfinance
  - [x] `fetch_analyst_info(ticker)` — Analyst recommendations and target prices from yfinance
  - [x] Cache with 30 min TTL (financials don't change intraday)

#### Tools

- [x] `src/stocksense/tools/financials.py` — MCP tool definitions
  - [x] `get_financials(ticker, statement="income")` — Return financial statement data
    - `statement` options: `income`, `balance_sheet`, `cash_flow`, `all`
    - Returns structured dict with annual data, rounded for LLM readability
    - Include key ratios: profit margin, ROE, debt/equity, current ratio, etc.
- [x] `src/stocksense/tools/analyze.py` — MCP tool definitions
  - [x] `analyze_company(ticker)` — Aggregate research brief
    - Current quote + price context (52-week range, % from high/low)
    - Key financial metrics (revenue, net income, margins, growth)
    - Recent insider trading summary (net buys vs sells)
    - Recent SEC filings (latest 10-K/10-Q dates)
    - Analyst consensus (target price, recommendation)
    - All data structured for LLM to generate bull/bear thesis

#### Server Registration

- [x] `src/stocksense/server.py` — Register `financials` and `analyze_company` tools

#### Tests

- [x] `tests/test_financials.py` — 8 tests
  - [x] Test income statement returns valid data
  - [x] Test balance sheet returns valid data
  - [x] Test cash flow returns valid data
  - [x] Test `statement="all"` returns all three
  - [x] Test invalid ticker handling
  - [x] Test invalid statement type handling
  - [x] Test ratios included
  - [x] Test tool output format
- [x] `tests/test_analyze.py` — 4 tests
  - [x] Test returns structured research brief with all sections
  - [x] Test price context computation
  - [x] Test insider summary aggregation
  - [x] Test invalid ticker graceful degradation

#### Docs

- [x] `README.md` — Add `financials` and `analyze_company` to tools table, update examples

### Key Decisions

- **yfinance for financials** — Free, no API key, covers income/balance/cash flow
- **No paid API dependency** — Keeps the project accessible to everyone
- **`analyze_company` is data aggregation, not LLM generation** — We collect and structure the data; the connected LLM does the analysis
- **Annual financials only** — Quarterly data is noisier and yfinance's quarterly coverage is inconsistent
- **Key ratios computed from raw data** — Profit margin, ROE, debt-to-equity, current ratio derived from statements

### Verification

1. `pytest` — All new + existing tests pass
2. In Claude Desktop: "Show me Apple's financial statements"
3. In Claude Desktop: "Give me a research brief on Tesla"
4. Existing tools still work (no regressions)
5. All planned tools from CLAUDE.md now implemented

---

## Milestone 4: Production Readiness & Packaging

**Status: COMPLETE**

Polish the project for public consumption: proper PyPI metadata, input validation, linting, MIT license.

### Action Items

- [x] `pyproject.toml` — Full PyPI metadata (description, keywords, classifiers, URLs, version constraints)
- [x] `src/stocksense/__init__.py` — Add `__version__`
- [x] `src/stocksense/tools/validation.py` — Input validation module
  - [x] Ticker format validation (regex, normalization)
  - [x] Period, interval, statement, limit validation with clear error messages
- [x] `src/stocksense/server.py` — Wire validation into all tool endpoints
- [x] `LICENSE` — MIT license file
- [x] `tests/test_validation.py` — 18 validation tests
- [x] Ruff linting — All lint issues fixed, 0 errors
- [x] All auto-fixable import sorting applied across codebase

### Key Decisions

- **Validation at server layer** — Tools get clean inputs, data layer stays simple
- **Clear error messages** — List valid options on invalid input
- **Ticker regex** — 1-5 letters, optional `.X` or `-X` suffix (handles BRK.B, BRK-B)
- **Limit caps** — Prevent excessive API calls (100 default, 50 for insider trades)

### Verification

1. `ruff check src/ tests/` — 0 errors
2. `pytest` — 59/59 tests pass
3. Invalid inputs return helpful error messages

---

## Milestone 5: CI/CD & Compare Tool

**Status: COMPLETE**

Add GitHub Actions CI pipeline and a company comparison tool for multi-ticker analysis.

### Action Items

- [x] `.github/workflows/ci.yml` — GitHub Actions CI
  - [x] Lint job (ruff on Python 3.11)
  - [x] Test job (unit tests on Python 3.11, 3.12, 3.13)
  - [x] Runs on push to main and PRs
- [x] `src/stocksense/tools/compare.py` — Company comparison tool
  - [x] `compare_companies(tickers)` — Side-by-side metrics comparison
  - [x] Fetches quote + financials for each ticker
  - [x] Graceful degradation on individual ticker failures
- [x] `src/stocksense/server.py` — Register `compare_companies` tool with validation
- [x] `tests/test_compare.py` — 4 comparison tests
- [x] `README.md` — Add `compare_companies` to tools table and examples

### Key Decisions

- **Unit tests only in CI** — Integration tests hit live APIs, unsuitable for CI
- **Max 10 tickers** — Prevents excessive API calls in a single comparison
- **Graceful partial failures** — If one ticker fails, others still return data

### Verification

1. `ruff check src/ tests/` — 0 errors
2. `pytest` — 63/63 tests pass
3. 8 tools registered in server

---

## Milestone 6: Earnings History & Company Profile

**Status: COMPLETE**

Add earnings history (EPS estimates vs actuals) and company profile (sector, industry, business description) tools. Enhance `analyze_company` to include earnings and profile data.

### Action Items

- [x] `src/stocksense/data/market.py` — Add data fetching
  - [x] `fetch_earnings_history(ticker)` — Quarterly EPS data from yfinance
  - [x] `fetch_sector_info(ticker)` — Sector, industry, employee count, business summary
- [x] `src/stocksense/tools/earnings.py` — `get_earnings` tool
- [x] `src/stocksense/tools/company_profile.py` — `get_company_profile` tool
- [x] `src/stocksense/tools/analyze.py` — Enhanced with earnings + profile sections
- [x] `src/stocksense/server.py` — Register `earnings` and `company_profile` tools
- [x] `tests/test_earnings.py` — 4 earnings tests
- [x] `tests/test_company_profile.py` — 4 company profile tests
- [x] `README.md` — Add new tools and example queries

### Verification

1. `ruff check src/ tests/` — 0 errors
2. `pytest` — 71/71 tests pass
3. 10 tools registered in server

---

## Milestone 7: Dividends & Key Events

**Status: COMPLETE**

Add dividend history/yield tool and upcoming key events (earnings dates, estimates, ex-dividend dates).

### Action Items

- [x] `src/stocksense/data/market.py` — Add data fetching
  - [x] `fetch_dividends(ticker)` — Dividend history, rate, yield, payout ratio
  - [x] `fetch_key_events(ticker)` — Upcoming earnings dates, EPS/revenue estimates, ex-dividend date
- [x] `src/stocksense/tools/dividends.py` — `get_dividends` tool
- [x] `src/stocksense/tools/events.py` — `get_key_events` tool
- [x] `src/stocksense/server.py` — Register `dividends` and `key_events` tools
- [x] `tests/test_dividends.py` — 4 dividend tests
- [x] `tests/test_events.py` — 4 events tests
- [x] `README.md` — Add new tools and example queries

### Verification

1. `ruff check src/ tests/` — 0 errors
2. `pytest` — 79/79 tests pass
3. 12 tools registered in server

---

## Milestone 8: Technical Indicators

**Status: COMPLETE**

Add technical analysis tool computing SMA, EMA, RSI, MACD, signals, and performance stats — all derived from existing price data with no new API calls.

### Action Items

- [x] `src/stocksense/data/technicals.py` — Technical indicator calculations
  - [x] SMA (20, 50, 200-day)
  - [x] EMA (12, 26-day)
  - [x] RSI (14-day)
  - [x] MACD (12/26/9)
  - [x] Performance stats (1w, 1m, 3m, 6m, YTD)
  - [x] Trading signals (overbought/oversold, MA crossovers)
- [x] `src/stocksense/tools/technicals.py` — `get_technicals` tool
- [x] `src/stocksense/server.py` — Register `technicals` tool
- [x] `tests/test_technicals.py` — 11 tests (unit + integration)
- [x] `README.md` — Add new tool and example queries

### Key Decisions

- **No external dependencies** — All indicators computed from price data using stdlib math
- **Signals included** — Human-readable "overbought"/"oversold"/"neutral" and MA crossover signals
- **Performance stats** — 1w, 1m, 3m, 6m, YTD percentage returns

### Verification

1. `ruff check src/ tests/` — 0 errors
2. `pytest` — 90/90 tests pass
3. 13 tools registered in server
