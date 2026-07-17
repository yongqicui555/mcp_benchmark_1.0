# Tool reference

The Halal Terminal MCP server exposes **22 tools** organized into 8 functional groups. All tools return JSON-encoded strings.

> Authentication is enforced at the SSE transport layer — every tool call requires a valid `X-API-Key`.

## Screening

### `screen_stock(symbol: str)`
Screen a stock for Shariah (Islamic law) compliance. Returns business-activity screening, financial-ratio checks against 5 methodologies (AAOIFI, DJIM, FTSE, MSCI, S&P), purification rate, and key financial metrics.

Use when asked *"Is [stock] halal?"* or *"Is [stock] Shariah-compliant?"*.

### `get_screening_result(symbol: str)`
Get a **cached** screening result without triggering a new screening. Faster than `screen_stock` but may return stale data.

Use when freshness isn't critical, or when checking a stock that was recently screened.

### `get_all_screening_results()`
List every stock that has been screened, sorted by most recent.

Use when the user asks *"What stocks have you already screened?"* or wants a history of past verdicts.

### `screen_etf(symbol: str, force_refresh: bool = False)`
Screen an ETF by analyzing every underlying holding. Returns per-holding compliance, overall verdict, compliant percentage, and aggregate purification rate.

Use when asked *"Is [ETF] halal?"* or *"How Shariah-compliant is [ETF]?"*.

### `bulk_screen(action: str, ...)`
Manage bulk screening of entire market indices (S&P 500, NASDAQ-100, FTSE-100, …). The `action` parameter dispatches to:

| Action | Required args | Purpose |
|---|---|---|
| `trigger` | `index_name` | Start screening an index |
| `status` | optional `run_id` | Status of a run (latest if omitted) |
| `list_runs` | — | List all runs |
| `results` | `run_id` | Paginated results, filterable by `compliant` / `methodology` / `sector` |
| `summary` | `run_id` | Aggregate stats for a run |
| `cancel` | `run_id` | Cancel a running screening |
| `compare` | `run_id="id1,id2"` | Diff two runs |
| `list_indices` | — | Available indices |

Use when screening an entire index, filtering for compliant-only names, or comparing two screening runs. **Note: index runs consume many tokens — check `list_indices` and `summary` before triggering a full run.**

## Market data

### `get_quote(symbol?: str, symbols?: list[str])`
Real-time quote(s) — price, change, volume, market cap, P/E, dividend yield. Pass `symbols` for batch queries; `symbol` is ignored when `symbols` is provided.

Use when asked for a current price, market cap, or P/E ratio.

### `get_stock_info(symbol: str, full: bool = False)`
Reference data for a stock (sector, exchange, description). With `full=True`, also returns the latest quote and screening result in one response (slower but more complete).

Use when the user asks about a company's profile, sector, or exchange listing.

### `get_price_history(symbol: str, period: str, interval: str)`
Historical OHLC data.

- `period` ∈ `1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max`
- `interval` ∈ `1m, 5m, 15m, 1h, 1d, 1wk, 1mo`

Use when asked for a chart, historical performance, or to plot price over time.

### `get_trending_stocks(limit: int = 10)`
Biggest movers — price, % change, volume. Returns up to 16 stocks.

Use when asked *"What's trending today?"* or *"What are the biggest movers?"*.

### `search_stocks(query, asset_type?, sector?, country?, exchange?, limit?)`
Search the catalog by name, ticker fragment, sector, country, or exchange. `asset_type` ∈ `equities` (default), `etf`.

Use when the user provides a company name or partial ticker and needs the correct symbol.

## ETF analysis

### `get_etf_info(symbol: str, data_type: str)`
ETF fund metadata or full holdings breakdown.

- `data_type="holdings"` — every underlying stock with weights
- `data_type="fund_info"` — expense ratio, total assets, inception date, etc.

Use when the user wants to inspect what a specific ETF holds or compare fund-level metadata.

### `etf_purification(symbol, investment_amount, dividend_income?)`
Compute the purification amount (donate the impure portion) for an ETF investment, based on its holdings-level compliance.

Use when asked *"How much of my ETF dividend income should I purify?"*.

### `compare_etfs(symbols: list[str])`
Side-by-side comparison of 2–5 ETFs: compliance analysis, expense ratios, and holdings-overlap detection.

Use when asked to compare two or more ETFs (e.g. *"SPUS vs HLAL vs QQQ"*).

## Portfolio & watchlist

### `scan_portfolio(symbols: list[str], force_refresh: bool = False)`
Screen up to **100** stocks at once. Returns per-stock compliance and an aggregate summary (compliant count, non-compliant count, average purification rate).

Use when the user provides a list of holdings and asks *"Is my portfolio halal?"* or *"Which of these are non-compliant?"*.

### `manage_watchlist(action, name?, watchlist_id?, symbol?, symbols?)`
CRUD on stock watchlists. `action` ∈ `create | list | get | add_symbol | remove_symbol | delete`.

Use when the user wants to save, view, or modify a named list of stocks to track.

## Comparison

### `compare_stocks(symbols: list[str])`
Compare 2–5 stocks side-by-side on Shariah compliance, financial ratios, market data, and metadata.

Use when asked *"Compare [A] vs [B]"* or *"Which of these is more Shariah-compliant?"*.

## Income & zakat

### `get_dividends(symbol: str, include_purification: bool = False)`
Dividend history. With `include_purification=True`, computes the purification amount per dividend based on the stock's non-compliant revenue ratio.

Use when asked for dividend history, or *"How much should I purify from my [stock] dividends?"*.

### `calculate_zakat(calculation_type, holdings, gold_price_per_gram?)`
Calculate obligatory charity (`zakat`) or impure income (`purification`) on stock holdings.

- `calculation_type="zakat"` → 2.5% of eligible wealth above the nisab threshold. `holdings` items: `{"symbol": "AAPL", "market_value": 10000}`
- `calculation_type="purification"` → impure dividend income. `holdings` items: `{"symbol": "AAPL", "dividend_income": 500}`
- `gold_price_per_gram` (USD, default `65.0`) — used only for the zakat nisab threshold.

Use when asked *"How much zakat do I owe on my portfolio?"* or to compute purification across multiple holdings at once.

## News & filings

### `get_news(symbol?, source?, category?, query?, page?, limit?)`
Financial and Islamic-finance news. Stock-specific when `symbol` is set; otherwise the general feed with optional filters. Articles include title, source, date, URL, and relevance metadata.

Use when asked for recent news about a stock, or for general Islamic-finance news.

### `get_sec_filings(symbol, data_type, filing_type?, limit?)`
SEC EDGAR data for US-listed companies.

- `data_type="filings"` — filing history (10-K, 10-Q, 8-K, …); use `filing_type` to filter
- `data_type="facts"` — structured XBRL data (revenue, assets, debt figures)

Use when the user wants to inspect a company's filings or verify financial facts from source documents.

## Reports & education

### `generate_report(report_type, symbol?, symbols?)`
Formatted Shariah screening report, ready to share or save.

- `report_type="screening"` — single-stock deep dive (requires `symbol`)
- `report_type="portfolio"` — multi-stock portfolio compliance (requires `symbols`)

Use when the user asks for a printable or shareable compliance summary.

### `islamic_finance_education(topic, query?, methodology_name?)`
Educational content about Islamic finance and Shariah screening. `topic` ∈:

- `glossary` — Islamic finance terms dictionary; filter with `query`
- `methodologies` — overview of all 5 Shariah screening methodologies
- `methodology_detail` — deep dive into one methodology (requires `methodology_name`)
- `screening_criteria` — financial ratio thresholds used in each methodology
- `purification_guide` — how to calculate and purify impure investment income

Use when asked *"What is zakat?"*, *"How does AAOIFI screen stocks?"*, or any Islamic-finance definition question.
