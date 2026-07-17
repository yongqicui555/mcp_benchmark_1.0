<div align="center">

# QuantRisk

**Institutional-grade portfolio risk analytics for Claude and any MCP client.**

[![npm version](https://img.shields.io/npm/v/@quantrisk/mcp-server.svg)](https://www.npmjs.com/package/@quantrisk/mcp-server)
[![npm downloads](https://img.shields.io/npm/dm/@quantrisk/mcp-server.svg)](https://www.npmjs.com/package/@quantrisk/mcp-server)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-brightgreen.svg)](https://modelcontextprotocol.io)

VaR / Monte Carlo / Stress Testing / Portfolio Optimization / Greeks / Correlation Matrices

Real market data. Real math. Not hallucinated numbers.

[Website](https://quantrisk.dev) · [Get Pro](https://quantrisk.dev/pricing) · [Documentation](https://quantrisk.dev/docs)

</div>

---

## Quick Start

**1. Install**

```bash
npm install -g @quantrisk/mcp-server
```

**2. Configure** (Claude Desktop — see [below](#configuration) for Cursor)

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "quantrisk": {
      "command": "quantrisk-mcp-server",
      "env": {
        "QUANTRISK_API_KEY": "your-api-key"
      }
    }
  }
}
```

Get your free API key at [quantrisk.dev/signup](https://quantrisk.dev/signup).

**3. Ask Claude**

> "What's the Value at Risk on a portfolio of 60% SPY, 25% TLT, and 15% GLD?"

That's it. Claude now has access to institutional-grade risk analytics.

---

## Configuration

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "quantrisk": {
      "command": "quantrisk-mcp-server",
      "env": {
        "QUANTRISK_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Cursor

Add to `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "quantrisk": {
      "command": "quantrisk-mcp-server",
      "env": {
        "QUANTRISK_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Any MCP Client

QuantRisk works with any client that supports the [Model Context Protocol](https://modelcontextprotocol.io). Point it at the `quantrisk-mcp-server` binary with your API key in the environment.

---

## Tools

| Tool | Description | Tier |
|------|-------------|------|
| `analyze_risk` | VaR, CVaR, volatility, Sharpe ratio, max drawdown | Free |
| `monte_carlo_simulation` | Forward-looking return simulations with configurable paths | Free |
| `stress_test` | Portfolio impact under historical and hypothetical scenarios | Free |
| `price_history` | Historical price and return data for any supported ticker | Free |
| `sector_exposure` | Sector and industry breakdown across holdings | Free |
| `performance_attribution` | Return attribution by asset, sector, and factor | Free |
| `correlation_matrix` | Cross-asset correlation analysis | Free |
| `optimize_portfolio` | Mean-variance and risk-parity optimization | **Pro** |
| `compare_portfolios` | Side-by-side risk/return comparison of multiple portfolios | **Pro** |
| `calculate_greeks` | Options Greeks — delta, gamma, theta, vega, rho | **Pro** |

---

## Example Queries

Once configured, ask Claude questions like these:

- **"Run a Monte Carlo simulation on my portfolio: 50% AAPL, 30% MSFT, 20% NVDA. Show me the 5th percentile outcome."**
- **"Stress test 70% VTI / 30% BND against the 2008 financial crisis and a hypothetical 300bp rate shock."**
- **"What's my sector exposure if I hold equal weights in AMZN, JPM, JNJ, XOM, and NEE?"**
- **"Show me the correlation matrix for SPY, GLD, TLT, and BTC-USD over the last 2 years."**
- **"Compare the risk-adjusted returns of a 60/40 portfolio vs. an all-weather portfolio."** *(Pro)*
- **"Calculate the Greeks for a SPY 550 call expiring in 30 days."** *(Pro)*

---

## Why Pro?

The free tier covers core risk analytics for small portfolios. Pro unlocks the tools and scale that serious analysis demands.

| | Free | Pro ($29/mo) |
|---|---|---|
| **Positions** | 20 | 500 |
| **API calls** | 50/day | Unlimited |
| **Tools** | 7 | All 10 |
| **Monte Carlo paths** | 1,000 | 100,000 |
| **Portfolio optimization** | — | Mean-variance, risk-parity, min-volatility |
| **Portfolio comparison** | — | Side-by-side multi-portfolio analysis |
| **Options Greeks** | — | Full Greeks surface |

**What that means in practice:**

- Free: "What's the VaR on my 10-stock portfolio?" — works great.
- Pro: "Optimize my 200-position portfolio for maximum Sharpe, then stress test it against 5 scenarios and compare it to my current allocation." — you need Pro for that.

[Upgrade to Pro](https://quantrisk.dev/pricing)

---

## How It Works

```
Claude / MCP Client
      |
  MCP Protocol
      |
QuantRisk MCP Server (local process)
      |
QuantRisk API (Cloudflare Workers)
      |
Yahoo Finance (market data) + risk engine (math)
```

- **MCP Server** runs locally as a stdio process — your API key never leaves your machine except to authenticate with the QuantRisk API.
- **Risk Engine** runs on Cloudflare Workers. All calculations — VaR, Monte Carlo, optimization — happen server-side with real math on real market data.
- **Market Data** sourced from Yahoo Finance. Prices, fundamentals, and options chains are fetched in real time.
- **Reports** generated with pdf-lib when applicable.

No data is stored. No portfolio information is retained after a request completes.

---

## Contributing

Contributions are welcome. Please open an issue first to discuss what you'd like to change.

```bash
git clone https://github.com/78degrees/mcp-server.git
cd mcp-server
npm install
npm test
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

[MIT](LICENSE)

---

<div align="center">

Built by the team at [quantrisk.dev](https://quantrisk.dev)

Contact: hello@quantrisk.dev

</div>
