[![PyPI](https://img.shields.io/pypi/v/meridianedge)](https://pypi.org/project/meridianedge/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Compatible-blue)](https://modelcontextprotocol.io)

# Meridian Edge MCP Server

Query real-time prediction market consensus data directly from Claude and other AI assistants via the [Model Context Protocol](https://modelcontextprotocol.io).

Ask Claude: *"What does the prediction market say about the Lakers game tonight?"* and get a live answer.

---

## What It Does

This MCP server gives Claude access to **Meridian Edge** — aggregated prediction market consensus data from multiple regulated prediction markets, updated every 10 minutes.

**5 tools available to Claude:**

| Tool | What it returns |
|------|----------------|
| `get_consensus` | Aggregated consensus probabilities for sports/politics events |
| `get_opportunities` | Events where prediction markets show notable divergence |
| `get_signals` | Recent directional market moves |
| `get_markets` | Active markets currently being tracked |
| `get_settlements` | Recently settled events with verified outcomes |

---

## Quick Start

### Option 1 — uvx (recommended, no install)

```json
{
  "mcpServers": {
    "meridian-edge": {
      "command": "uvx",
      "args": ["meridian-edge-mcp"]
    }
  }
}
```

### Option 2 — pip install

```bash
pip install meridian-edge-mcp
```

```json
{
  "mcpServers": {
    "meridian-edge": {
      "command": "meridian-edge-mcp"
    }
  }
}
```

### Option 3 — run from source

```bash
git clone https://github.com/meridian-edge/meridian-edge-mcp
cd meridian-edge-mcp
pip install -e .
```

```json
{
  "mcpServers": {
    "meridian-edge": {
      "command": "python",
      "args": ["-m", "meridian_edge_mcp.server"]
    }
  }
}
```

---

## Configure Claude Desktop

Open your Claude Desktop config file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Add the `meridian-edge` entry to `mcpServers`:

```json
{
  "mcpServers": {
    "meridian-edge": {
      "command": "uvx",
      "args": ["meridian-edge-mcp"],
      "env": {
        "MERIDIAN_EDGE_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

Restart Claude Desktop. You'll see the Meridian Edge tools listed in Claude's tool panel.

### Cursor IDE

Add to `.cursor/mcp.json`:

```json
{
  "meridian-edge": {
    "command": "uvx",
    "args": ["meridian-edge-mcp"]
  }
}
```

### Windsurf IDE

Add to Windsurf MCP config:

```json
{
  "meridian-edge": {
    "command": "uvx",
    "args": ["meridian-edge-mcp"]
  }
}
```

---

## Try It Now

Ask Claude:
- "What's the prediction market consensus on the Lakers game?"
- "Show me events where prediction markets disagree"
- "What markets settled today?"

Example response:
```
Lakers vs Celtics
  Consensus: 62% (YES)
  Sources: 5 regulated markets
  Confidence: HIGH
  Spread: 8.3%
```

---

## API Key

The server works out of the box with a free demo key (limited data).

For full access, get a **free API key** at [meridianedge.io](https://meridianedge.io) — no credit card required, instant signup.

Set it as an environment variable:

```bash
export MERIDIAN_EDGE_API_KEY=your_key_here
```

Or in your Claude Desktop config (see above).

**Free tier:** 100 calls/day — enough for personal use.

---

## Example Prompts

Once configured, ask Claude:

**Game consensus:**
> "What's the prediction market consensus on tonight's NBA games?"

> "What are prediction markets saying about the Lakers vs Warriors?"

> "Show me NFL prediction market probabilities for this week"

**Divergence / opportunities:**
> "Which prediction markets are showing the most disagreement right now?"

> "Show me events where prediction markets disagree — NBA only"

> "What are today's highest-scoring divergence opportunities?"

**Signals:**
> "What prediction market signals fired in the last hour?"

> "Show me the most recent market moves"

**Markets:**
> "What prediction markets are active right now?"

> "List active NHL prediction markets"

**History:**
> "How did recent prediction market consensus perform? Show settled events"

> "What outcomes were predicted correctly in the last batch?"

---

## Example Output

```
PREDICTION MARKET CONSENSUS — NBA (3 events)

1. NBA: ATL vs DET (2026-03-25)
   Consensus: 46.6% YES  |  Spread: 1.6%  |  Confidence: MEDIUM
   Trend (30min): ↓ -23.3%  |  Platforms: 2  |  ▃▃▄▄▇▆
   Updated: 2026-03-26 01:15 UTC

2. NBA: BOS vs OKC (2026-03-25)
   Consensus: 39.0% YES  |  Spread: 1.2%  |  Confidence: LOW
   Trend (30min): ↑ +3.5%  |  Platforms: 2  |  ▆▆▆▆▆▄
   Updated: 2026-03-26 01:15 UTC

3. NBA: CLE vs MIA (2026-03-25)
   Consensus: 57.0% YES  |  Spread: 0.8%  |  Confidence: HIGH
   Trend (30min): → stable  |  Platforms: 2  |  ▆▆▆▇▇▇
   Updated: 2026-03-26 01:15 UTC

For informational purposes only. Not investment advice.
Source: Meridian Edge — meridianedge.io
```

---

## Data Coverage

- **Sports:** NBA, NFL, MLB, NHL, MLS, college sports, boxing
- **Politics:** US elections, ballot measures
- **Economics:** Federal Reserve rate decisions, macro indicator markets
- **Update frequency:** Every 10 minutes during active market hours

---

## Pricing

| Tier | Price | Calls/day | Features |
|------|-------|-----------|---------|
| **Free** | $0 | 100 | Consensus probabilities, active markets |
| **Starter** | $29/mo | 500 | + Opportunities, signals, spread data |
| **Pro** | $99/mo | 5,000 | + Fair value, platform breakdown, history |
| **Teams** | $499/mo | 50,000 | + Team seats, priority support |

[Full pricing →](https://meridianedge.io/#pricing)

---

## AI Platform Integrations

Use Meridian Edge consensus data directly inside major AI platforms — no code required:

| Platform | Link | Notes |
|----------|------|-------|
| **ChatGPT** | [Open Custom GPT](https://chatgpt.com/g/g-69c5cf29be388191aeaaf3159cd41697-prediction-market-consensus) | No setup — just open and ask |
| **Claude (this repo)** | [MCP install guide](https://github.com/meridian-edge/meridian-edge-mcp) | Claude Desktop / Cursor via MCP |
| **Gemini** | [Open Gem](https://gemini.google.com/gem/1aSpfo0atq00TWFEjDJLytxzsnqTdqHjJ) | No setup — just open and ask |

---

## Links

- [Dashboard](https://meridianedge.io/dashboard.html) — free, no signup required
- [API Documentation](https://meridianedge.io/docs.html)
- [AI Integrations](https://meridianedge.io/agents.html)
- [Embeddable Widget](https://meridianedge.io/widget.html)
- [Get Free API Key](https://meridianedge.io)

---

## Also Available On

- **[ChatGPT GPT Store](https://chatgpt.com/g/g-69c5cf29be388191aeaaf3159cd41697-prediction-market-consensus)** — Ask ChatGPT about prediction markets
- **[Google Gemini Gem](https://gemini.google.com/gem/1aSpfo0atq00TWFEjDJLytxzsnqTdqHjJ)** — Deep Research with prediction data
- **[Python SDK](https://pypi.org/project/meridianedge/)** — `pip install meridianedge`
- **[RapidAPI](https://rapidapi.com)** — REST API marketplace listing
- **[Dashboard](https://meridianedge.io/dashboard.html)** — Free, no signup
- **[API Docs](https://meridianedge.io/docs.html)** — Full endpoint reference
- **[Free API Key](https://meridianedge.io)** — 100 calls/day, no credit card

---

## License

MIT — see [LICENSE](LICENSE)

*For informational purposes only. Not investment advice. Data aggregated from publicly available prediction market sources. © 2026 VeraTenet LLC d/b/a Meridian Edge.*
