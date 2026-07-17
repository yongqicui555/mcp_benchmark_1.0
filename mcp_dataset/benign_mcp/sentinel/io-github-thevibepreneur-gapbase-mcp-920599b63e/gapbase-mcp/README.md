# gapbase-mcp

**Query 474 validated startup gaps from Claude Desktop, Cursor, and Windsurf.**

GapBase is a database of real pain points scraped from Reddit, LinkedIn, and X — each one a validated opportunity for a vibe-coded micro-SaaS. This MCP server lets you search the full database directly from your AI coding environment.

- 🗂️ **474 validated gaps** across 7 industries (ecommerce, healthcare, legal, accounting, property, dental, veterinary)
- 🧠 **Problem statement + vibe-code solution** for every gap
- 🔥 **5 weekly trending gaps** from live social signals (TikTok, HBO, viral challenges)
- 🚀 **Free, no signup, zero network calls** — everything runs locally
- 🔗 Each gap links to the full blueprint (tech stack, GTM, outreach templates) at [thevibepreneur.com](https://thevibepreneur.com)

## Install

```bash
npm install -g gapbase-mcp
```

Then add to your MCP client config:

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or the equivalent on your OS, and add:

```json
{
  "mcpServers": {
    "gapbase": {
      "command": "npx",
      "args": ["-y", "gapbase-mcp"]
    }
  }
}
```

Restart Claude Desktop. You should see a 🔌 icon indicating the server is connected.

### Cursor

Edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "gapbase": {
      "command": "npx",
      "args": ["-y", "gapbase-mcp"]
    }
  }
}
```

### Windsurf

Edit `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "gapbase": {
      "command": "npx",
      "args": ["-y", "gapbase-mcp"]
    }
  }
}
```

## Usage

Once installed, just ask your AI assistant questions in natural language:

> **"Find me 5 legal gaps about billing or time tracking."**
>
> **"What ecommerce gap targets Shopify merchants who want to leave Klaviyo?"**
>
> **"Show me this week's trending gaps with short build windows."**
>
> **"What are the top pain points in property management right now?"**
>
> **"Give me a dental gap I could vibe code this weekend."**

Claude / Cursor will automatically call the appropriate tool and return problem statements with vibe-code solution directions. Every result includes a `full_blueprint` URL pointing to the complete breakdown on thevibepreneur.com.

## Tools

| Tool | What it does |
|---|---|
| `list_industries` | 7 industries covered with gap counts per industry |
| `search_gaps` | Keyword and/or industry filtered search across 474 validated B2B gaps (the primary tool) |
| `get_gap` | Fetch a single gap by id or slug |
| `get_viral_social_gaps` | 5 weekly viral consumer trends (TikTok, HBO, short-window builds) — specialized, ask explicitly |
| `get_stats` | Database statistics and metadata |

## Philosophy

**Free MCP users get the diagnosis. The cure lives on the website.**

Each gap in the MCP bundle includes:
- Problem statement (what's broken)
- Vibe-code solution (a build direction)
- Industry + role
- `full_blueprint` URL with tech stack, difficulty, GTM playbook, and outreach templates

If you find a gap worth building, click through to the blueprint on thevibepreneur.com for the complete kit. [Founding Member access](https://thevibepreneur.com/discover?utm_source=mcp) unlocks the full 474 blueprints forever.

## Privacy

This MCP server runs **100% locally.** It does not phone home, does not track usage, does not collect any data about you, your queries, or your Claude conversations. The entire gap database is bundled in the npm package — no network calls, no API keys, no auth.

## About

Built by [The Vibepreneur](https://thevibepreneur.com). New gaps added weekly. Follow development and ship notes at [thevibepreneur.com/gaps](https://thevibepreneur.com/gaps).

## License

MIT
