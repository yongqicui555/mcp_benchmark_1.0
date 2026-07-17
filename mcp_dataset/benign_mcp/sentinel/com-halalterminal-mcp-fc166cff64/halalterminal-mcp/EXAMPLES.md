# Examples

End-to-end prompt walkthroughs for the most common Halal Terminal MCP use cases. Every example assumes the server is connected (see [CONNECT.md](CONNECT.md)).

---

## 1. Quick verdict on a single stock

> **You:** Is AAPL halal?

The agent calls `screen_stock(symbol="AAPL")` and replies with:

- Overall verdict per methodology (AAOIFI / DJIM / FTSE / MSCI / S&P)
- Business-activity check (no alcohol, gambling, conventional finance, …)
- Financial ratios (debt/market-cap, interest income, illiquid assets, …)
- **Purification rate** — the % of dividend income to donate

---

## 2. Audit an existing portfolio

> **You:** Audit my portfolio for Shariah compliance:
> AAPL 30%, MSFT 20%, JNJ 15%, V 15%, NESN 10%, BRK-B 10%

The agent calls `scan_portfolio(symbols=[...])` and produces:

- Per-stock verdict
- Aggregate compliant / non-compliant counts
- Average purification rate across the portfolio
- Suggestions for non-compliant positions

---

## 3. Calculate zakat on holdings

> **You:** Calculate zakat on these holdings:
> AAPL: $12,000 · MSFT: $8,000 · JNJ: $5,500 · V: $4,200

The agent calls:

```
calculate_zakat(
  calculation_type="zakat",
  holdings=[
    {"symbol": "AAPL", "market_value": 12000},
    {"symbol": "MSFT", "market_value":  8000},
    {"symbol": "JNJ",  "market_value":  5500},
    {"symbol": "V",    "market_value":  4200}
  ]
)
```

Reply includes the **nisab threshold** (computed from the gold price), eligible wealth above it, and the 2.5% zakat amount.

---

## 4. Purify dividend income

> **You:** I received $850 in dividends from AAPL last year. How much should I purify?

The agent calls `get_dividends(symbol="AAPL", include_purification=True)` (or `calculate_zakat` with `calculation_type="purification"`) and returns the impure-portion amount based on the stock's non-compliant revenue ratio.

---

## 5. Screen an ETF (SPY, QQQ, …)

> **You:** Is SPY Shariah-compliant? Compare it to ISDU.

The agent calls `screen_etf("SPY")`, `screen_etf("ISDU")`, then `compare_etfs(["SPY", "ISDU"])`. The reply covers:

- Compliant percentage of holdings
- Per-ETF expense ratio and AUM
- Holdings overlap
- Aggregate purification rate per dollar invested

---

## 6. Bulk-screen an entire index

> **You:** Screen the S&P 500 with the AAOIFI methodology and show me the top 20 compliant tech names by market cap.

The agent runs:

1. `bulk_screen(action="trigger", index_name="sp500")` → returns a `run_id`
2. `bulk_screen(action="status", run_id="...")` → poll until done
3. `bulk_screen(action="results", run_id="...", compliant=True, methodology="AAOIFI", sector="Technology", page_size=20)`

---

## 7. News watch on the portfolio

> **You:** Any news in the last week affecting compliance of my holdings?

The agent loops `get_news(symbol=...)` over each portfolio symbol, filters by date window, and surfaces compliance-relevant items (e.g. new debt issuance, M&A into a non-compliant sector, dividend policy changes).

---

## 8. Education — methodologies primer

> **You:** What's the difference between AAOIFI and MSCI?

The agent calls `islamic_finance_education(topic="methodology_detail", methodology_name="AAOIFI")` and `islamic_finance_education(topic="methodology_detail", methodology_name="MSCI")` and returns a side-by-side comparison of business-activity rules, financial-ratio thresholds, and treatment of mixed-revenue companies.

---

## Tips

- **Be explicit about percentages** when auditing portfolios — the agent uses them to compute weighted compliance metrics.
- **Cache-friendly tools** — `get_screening_result` returns the last cached verdict instantly; use it when freshness isn't critical.
- **Token budgeting** — `bulk_screen` of an index can cost hundreds of tokens. Start with `list_indices` and `summary` actions before kicking off a full run.
- **Multi-stock comparison** — `compare_stocks` and `compare_etfs` accept up to 5 symbols; for larger sets use `scan_portfolio`.
