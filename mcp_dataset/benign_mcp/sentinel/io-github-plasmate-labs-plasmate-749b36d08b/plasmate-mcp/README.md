# plasmate-mcp

MCP server for [Plasmate](https://plasmate.app) - the browser engine for AI agents.

Gives Claude Code, Claude Desktop, Cursor, Windsurf, and any MCP client the ability to browse the web through Plasmate instead of Chrome.

## Install

```bash
# Install the MCP wrapper
npm install -g plasmate-mcp

# Install the Plasmate engine (pick one)
pip install plasmate
# or: cargo install plasmate
# or: brew tap plasmate-labs/plasmate && brew install plasmate
```

## Use with Claude Code

```bash
claude mcp add plasmate -- npx plasmate-mcp
```

Or manually add to `~/.claude/settings.json`:
```json
{
  "mcpServers": {
    "plasmate": {
      "command": "npx",
      "args": ["-y", "plasmate-mcp"]
    }
  }
}
```

## Use with Claude Desktop

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "plasmate": {
      "command": "npx",
      "args": ["-y", "plasmate-mcp"]
    }
  }
}
```

## Use with Cursor

Add to Cursor's MCP settings:
```json
{
  "mcpServers": {
    "plasmate": {
      "command": "npx",
      "args": ["-y", "plasmate-mcp"]
    }
  }
}
```

## Available Tools

Once connected, your AI gets these tools:

| Tool | Description |
|------|-------------|
| `fetch_page` | Fetch a URL and get the Semantic Object Model (SOM) |
| `extract_text` | Get clean readable text from any URL |
| `open_page` | Open a persistent browser session |
| `click` | Click elements by SOM ID |
| `evaluate` | Execute JavaScript in the page |
| `close_page` | Close a browser session |

## Why Plasmate instead of Chrome?

- **16.6x fewer tokens** - SOM is dramatically smaller than DOM dumps
- **50x faster** - No rendering engine overhead
- **30MB memory** - vs Chrome's 300MB+
- **Structured output** - Clean JSON, not raw HTML

## Links

- [Plasmate](https://plasmate.app)
- [Documentation](https://docs.plasmate.app)
- [W3C Community Group](https://www.w3.org/community/web-content-browser-ai/)
- [GitHub](https://github.com/plasmate-labs/plasmate)


---

## Part of the Plasmate Ecosystem

| | |
|---|---|
| **Engine** | [plasmate](https://github.com/plasmate-labs/plasmate) - The browser engine for agents |
| **MCP** | [plasmate-mcp](https://github.com/plasmate-labs/plasmate-mcp) - Claude Code, Cursor, Windsurf |
| **Extension** | [plasmate-extension](https://github.com/plasmate-labs/plasmate-extension) - Chrome cookie export |
| **SDKs** | [Python](https://github.com/plasmate-labs/plasmate-python) / [Node.js](https://github.com/plasmate-labs/quickstart-node) / [Go](https://docs.plasmate.app/sdk-go) / [Rust](https://github.com/plasmate-labs/quickstart-rust) |
| **Frameworks** | [LangChain](https://github.com/langchain-ai/langchain/pull/36208) / [CrewAI](https://github.com/plasmate-labs/crewai-plasmate) / [AutoGen](https://github.com/plasmate-labs/autogen-plasmate) / [Smolagents](https://github.com/plasmate-labs/smolagents-plasmate) |
| **Tools** | [Scrapy](https://github.com/plasmate-labs/scrapy-plasmate) / [Audit](https://github.com/plasmate-labs/plasmate-audit) / [A11y](https://github.com/plasmate-labs/plasmate-a11y) / [GitHub Action](https://github.com/plasmate-labs/som-action) |
| **Resources** | [Awesome Plasmate](https://github.com/plasmate-labs/awesome-plasmate) / [Notebooks](https://github.com/plasmate-labs/notebooks) / [Benchmarks](https://github.com/plasmate-labs/plasmate-benchmarks) |
| **Docs** | [docs.plasmate.app](https://docs.plasmate.app) |
| **W3C** | [Web Content Browser for AI Agents](https://www.w3.org/community/web-content-browser-ai/) |
