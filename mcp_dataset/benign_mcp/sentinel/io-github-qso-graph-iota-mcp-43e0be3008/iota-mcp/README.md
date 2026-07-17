<!-- mcp-name: io.github.qso-graph/iota-mcp -->
# iota-mcp

MCP server for [Islands on the Air (IOTA)](https://www.iota-world.org/) — group lookup, island search, DXCC mapping, nearby groups, and programme statistics through any MCP-compatible AI assistant.

Part of the [qso-graph](https://qso-graph.io/) project. **No authentication required** — all IOTA data is public.

## Install

```bash
pip install iota-mcp
```

## Tools

| Tool | Description |
|------|-------------|
| `iota_lookup` | Look up an IOTA group by reference number (e.g., NA-005) |
| `iota_search` | Search groups and islands by name (e.g., Hawaii, Shetland) |
| `iota_islands` | List all islands and subgroups in an IOTA group |
| `iota_dxcc` | Bidirectional DXCC-to-IOTA mapping |
| `iota_stats` | Programme summary — totals by continent, most/least credited |
| `iota_nearby` | Find IOTA groups nearest to a lat/lon location |
| `get_version_info` | Service version + upstream programme data version (fleet identity attestation) |

## Quick Start

No credentials needed — just install and configure your MCP client.

### Configure your MCP client

iota-mcp works with any MCP-compatible client. Add the server config and restart — tools appear automatically.

#### Claude Desktop

Add to `claude_desktop_config.json` (`~/Library/Application Support/Claude/` on macOS, `%APPDATA%\Claude\` on Windows):

```json
{
  "mcpServers": {
    "iota": {
      "command": "iota-mcp"
    }
  }
}
```

#### Claude Code

Add to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "iota": {
      "command": "iota-mcp"
    }
  }
}
```

#### ChatGPT Desktop

```json
{
  "mcpServers": {
    "iota": {
      "command": "iota-mcp"
    }
  }
}
```

#### Cursor

Add to `.cursor/mcp.json` (project-level) or `~/.cursor/mcp.json` (global):

```json
{
  "mcpServers": {
    "iota": {
      "command": "iota-mcp"
    }
  }
}
```

#### VS Code / GitHub Copilot

Add to `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "iota": {
      "command": "iota-mcp"
    }
  }
}
```

#### Gemini CLI

Add to `~/.gemini/settings.json` (global) or `.gemini/settings.json` (project):

```json
{
  "mcpServers": {
    "iota": {
      "command": "iota-mcp"
    }
  }
}
```

### Example Prompts

- "Look up IOTA group NA-005"
- "Search for islands named Shetland"
- "What IOTA groups are near Boise, Idaho?"
- "Show me all islands in EU-005"
- "What IOTA references map to DXCC 291?"
- "Give me IOTA programme statistics"

## Data Source

Data comes from the official [IOTA website](https://www.iota-world.org/) JSON downloads:

- **fulllist.json** — complete group/subgroup/island hierarchy (~1.3 MB)
- **dxcc_matches_one_iota.json** — 1:1 DXCC-to-IOTA mapping (~3.5 KB)

Data is downloaded once and cached for 24 hours (IOTA refreshes daily at 00:00 UTC).

## Development

```bash
git clone https://github.com/qso-graph/iota-mcp.git
cd iota-mcp
pip install -e .

# Run with mock data (no network)
IOTA_MCP_MOCK=1 python -m iota_mcp.server

# Run with MCP Inspector
iota-mcp --transport streamable-http --port 8010

# Security tests
pip install pytest
pytest tests/test_security.py -v
```

## License

GPL-3.0-or-later
