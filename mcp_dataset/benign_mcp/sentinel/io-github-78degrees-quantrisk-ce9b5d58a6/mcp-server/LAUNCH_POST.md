# I Built a Portfolio Risk Analytics MCP That No One Else Has — Here's Why

*Published on Dev.to | ~800 words*

---

There are 10,000+ MCP servers. Zero of them compute portfolio risk.

I spent two weeks researching the MCP ecosystem before writing a single line of code. I crawled PulseMCP, mcp.so, Smithery, Glama, and the Anthropic MCP Registry. I read every "I built a profitable MCP" post I could find. I mapped the competitive landscape in a spreadsheet.

The result: a complete picture of what's been built, what's selling, and what's missing.

The gap that jumped off the page was financial analytics. Not trading data feeds — those exist, some are decent. I mean the *computation* layer. The thing that takes your positions, fetches prices, and tells you: here's your Value at Risk, here's what happens to your portfolio if 2008 happens again, here's the optimal allocation given your constraints.

That tool did not exist. Today it does.

---

## What Was There (and Why It Wasn't Enough)

The best financial MCPs I found were glorified API wrappers. Pass a ticker, get back raw price data. That's useful for context — Claude can reason about "AAPL closed at $192 yesterday" — but it doesn't solve the actual problem quant traders have.

A quant trader's real questions are:

- What's my downside exposure right now, across the whole book?
- If I run 10,000 Monte Carlo paths on this allocation, what does the distribution of outcomes look like?
- How would my positions have performed during COVID? During 2008? During the dot-com crash?
- Given these 15 tickers, what allocation maximizes my Sharpe ratio subject to my constraints?

None of those questions can be answered by fetching a price. They require computation — matrix math, historical simulations, numerical optimization, Black-Scholes. And they require that computation to happen server-side, with results the AI can actually reason about.

That's the gap. That's what I built.

---

## What QuantRisk Does

QuantRisk is an MCP server with 10 tools covering the full stack of portfolio risk analytics:

**`analyze_risk`** — The workhorse. Pass your positions, get back VaR (historical, parametric, or Cornish-Fisher), CVaR/Expected Shortfall, annualized volatility, beta, and max drawdown. Sensible defaults (95% confidence, 1-day horizon) mean you can just say "what's my risk?" and get a useful answer.

**`monte_carlo_simulation`** — GBM and jump-diffusion paths, up to 100,000 simulations, percentile outcomes from p1 to p99, probability of loss, expected shortfall in the worst 5% of paths.

**`stress_test`** — Eight historical crisis scenarios baked in: GFC 2008, COVID crash, dot-com 2000, Black Monday 1987, Taper Tantrum, 2022 rate hike cycle, Volmageddon, European debt crisis. Pro tier adds custom shocks where you define the factor returns yourself.

**`optimize_portfolio`** — Markowitz mean-variance optimization with three objectives: maximum Sharpe, minimum variance, or target return. Includes the full efficient frontier so you can see the risk/return tradeoff across allocations.

**`calculate_greeks`** — Delta, gamma, theta, vega, rho for European (Black-Scholes) and American (binomial tree) options. Portfolio-level aggregate Greeks included.

Plus `correlation_matrix`, `performance_attribution` (Sharpe, Sortino, Treynor, Calmar, Information ratio), `sector_exposure`, `price_history`, and `compare_portfolios`.

Every tool returns a `summary` field — a human-readable paragraph Claude can present directly without further processing. The AI never has to parse a number to give you an answer.

---

## Technical Decisions

**TypeScript on Cloudflare Workers.** The latency requirements for MCP tools are unforgiving — users are waiting in a live conversation. Workers deploy to Cloudflare's global edge and cold-start in microseconds, not hundreds of milliseconds. TypeScript because the MCP SDK is TypeScript-first and the type safety matters when you're implementing financial math.

**Stateless architecture.** No portfolio IDs, no "create portfolio first" workflow. Every tool call includes the positions array inline. This is the right design for MCP: the AI builds the positions from conversation context and passes them in. No session management, no state synchronization bugs, no "your portfolio has expired" errors.

**Cloudflare KV for price caching.** Daily price data is cached at the edge with a 24-hour TTL. This eliminates repeated Alpha Vantage calls for the same ticker within a trading day, keeps latency low, and protects against upstream rate limits.

**Durable Objects for tier enforcement.** Each API key maps to a Durable Object that stores tier status, Stripe subscription ID, and usage counters. Rate limiting uses the alarm API for atomic daily resets. No race conditions, no Redis to manage.

---

## Pricing Rationale

Free tier is genuinely useful: 7 of 10 tools, 20 positions, 1,000 Monte Carlo paths, 100 calls/day. A retail trader with a small portfolio can get real value without paying anything.

Pro is $29/month. This unlocks the three most compute-intensive tools (optimize, compare, Greeks), raises all limits to levels that support active professional use (500 positions, 100K paths, 5,000 calls/day), and adds custom stress scenarios and full factor attribution.

$29/month is cheap for what it replaces. A Bloomberg terminal seat is $24,000/year. A standalone Monte Carlo simulation tool costs more than this. The goal is to be priced at "obviously worth it for anyone actually using it" — not maximum extraction.

---

## Try It Now

```bash
npm install -g @quantrisk/mcp-server
```

Get a free API key at [quantrisk.dev](https://quantrisk.dev). Add the config to Claude Desktop or Cursor (one JSON block, 30 seconds). Then ask your AI assistant: *"I have 100 shares of AAPL and 200 shares of MSFT — what's my portfolio's VaR at 95% confidence?"*

The answer will come back in seconds, not a link to a spreadsheet template.

The code is MIT licensed and on GitHub at [github.com/quantrisk/mcp-server](https://github.com/quantrisk/mcp-server). Issues, pull requests, and brutal feedback all welcome — especially from quant practitioners who know what's missing.

---

*Tags: mcp, finance, typescript, cloudflare, quantitative-finance, portfolio-management*
