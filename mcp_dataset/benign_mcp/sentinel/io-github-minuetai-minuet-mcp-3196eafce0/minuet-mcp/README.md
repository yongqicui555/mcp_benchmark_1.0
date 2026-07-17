# minuet-mcp

An [MCP](https://modelcontextprotocol.io) server for [Minuet](https://minuet.ai) — the relationship layer for ERC-8004 AI agents.

Exposes Minuet's read-only API as a set of MCP tools so any MCP-compatible client (Claude Desktop, Cursor, Cline, etc.) can query the ERC-8004 agent relationship graph natively.

## What it exposes

| Tool | Purpose |
| --- | --- |
| `search_agents` | Search indexed ERC-8004 agents by name |
| `get_agent` | Fetch full agent detail + relationships |
| `get_agent_relationships` | List one agent's relationships (incoming/outgoing/both) |
| `get_hub_agents` | Most-connected agents in the graph |
| `get_owner_ecosystems` | Owners who operate multiple connected agents |
| `get_relationship_graph` | The full relationship edge list |
| `get_network_stats` | Aggregate totals (relationships, agents, statuses, types) |
| `get_recent_relationships` | Most recently created relationships |

All tools are read-only. Write operations (claim, propose, confirm) are wallet-gated on minuet.ai and are not exposed via MCP.

## Install

Requires Python 3.10+.

```bash
pipx install minuet-mcp
# or run ephemerally:
uvx minuet-mcp
```

## Use with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "minuet": {
      "command": "uvx",
      "args": ["minuet-mcp"]
    }
  }
}
```

Restart Claude Desktop. The Minuet tools will appear in the tool picker.

## Use with Cursor / Cline

Point your MCP config at the `minuet-mcp` binary (installed via `pipx`) or `uvx minuet-mcp` and the tools will be discovered automatically.

## Configuration

| Env var | Default | Purpose |
| --- | --- | --- |
| `MINUET_API_URL` | `https://minuet.ai` | Base URL of the Minuet API. Override for local development. |

## About Minuet

Minuet is the relationship layer for ERC-8004 AI agents. ERC-8004 gives agents on-chain identity; A2A gives them tasks; x402 gives them payments. Minuet is where two agent owners formally record, verify, and manage their working relationship.

- Website: [minuet.ai](https://minuet.ai)
- Relationship artifact: [minuet.ai/relationships](https://minuet.ai/relationships)

## License

MIT

<!-- mcp-name: io.github.minuetai/minuet-mcp -->

