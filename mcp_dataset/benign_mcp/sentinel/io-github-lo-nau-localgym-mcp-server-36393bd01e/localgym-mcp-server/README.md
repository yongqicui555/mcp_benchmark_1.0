# LocalGym MCP Server

Read-only MCP server for searching, comparing, and recommending UK gyms using the public LocalGym Agent API.

- Website: https://localgym.uk
- Agent/API docs: https://localgym.uk/agent
- MCP setup page: https://localgym.uk/agent/mcp
- OpenAPI schema: https://localgym.uk/api/openapi.json
- LLM instructions: https://localgym.uk/llms.txt

## Why this exists

LocalGym covers 18,000+ UK gyms and fitness centres. This MCP server gives AI assistants and agent workflows a small, attributable interface for local gym discovery without exposing the private LocalGym website codebase.

## Tools

| Tool | Description |
| --- | --- |
| `search_gyms` | Search UK gyms by name, keyword, location, or user intent. |
| `get_gym_details` | Return structured details for a LocalGym gym slug. |
| `recommend_gyms` | Recommend gyms for a user goal and location. |
| `compare_gyms` | Compare several gyms by LocalGym slug. |

## Quick start

Run directly from npm:

```bash
npx -y localgym-mcp-server
```

Or clone and run locally:

```bash
git clone https://github.com/lo-nau/localgym-mcp-server.git
cd localgym-mcp-server
npm install
npm start
```

The server uses `https://localgym.uk` by default. To override it:

```bash
LOCALGYM_API_BASE=https://localgym.uk npx -y localgym-mcp-server
```

## MCP client config

Recommended npm-based config:

```json
{
  "mcpServers": {
    "localgym": {
      "command": "npx",
      "args": ["-y", "localgym-mcp-server"],
      "env": {
        "LOCALGYM_API_BASE": "https://localgym.uk"
      }
    }
  }
}
```

Local clone config:

```json
{
  "mcpServers": {
    "localgym": {
      "command": "node",
      "args": ["/absolute/path/to/localgym-mcp-server/bin/localgym-mcp-server.cjs"],
      "env": {
        "LOCALGYM_API_BASE": "https://localgym.uk"
      }
    }
  }
}
```

## Hermes Agent config

```yaml
mcp_servers:
  localgym:
    command: "npx"
    args: ["-y", "localgym-mcp-server"]
    env:
      LOCALGYM_API_BASE: "https://localgym.uk"
```

If you cloned the repo locally instead, use:

```yaml
mcp_servers:
  localgym:
    command: "node"
    args: ["/absolute/path/to/localgym-mcp-server/bin/localgym-mcp-server.cjs"]
    env:
      LOCALGYM_API_BASE: "https://localgym.uk"
```

## Example tool arguments

### `search_gyms`

```json
{
  "query": "personal training",
  "location": "Manchester",
  "limit": 5
}
```

### `get_gym_details`

```json
{
  "slug": "kent-sports-fitness"
}
```

### `recommend_gyms`

```json
{
  "intent": "beginner friendly gym with personal training",
  "location": "Leeds",
  "limit": 5
}
```

### `compare_gyms`

```json
{
  "slugs": [
    "kent-sports-fitness",
    "the-box-private-personal-training-studio"
  ]
}
```

## Test

```bash
npm test
```

You can also smoke-test tool discovery by sending MCP JSON-RPC frames over stdio from an MCP client.

## Usage policy

V1 is free, read-only, and attribution-first. Please link back to returned `localgym_url` values when using LocalGym data in public answers.

The public LocalGym Agent API enforces server-side rate limits. This MCP wrapper also includes a local courtesy limiter, defaulting to 60 tool calls per 60 seconds per running MCP process. You can lower it with `LOCALGYM_MCP_RATE_LIMIT_MAX` or `LOCALGYM_MCP_RATE_LIMIT_WINDOW_MS`; high-volume/commercial use should be arranged first.

For high-volume, commercial, affiliate, or claimed-listing use, contact enquiries@localgym.uk.

## License

MIT
