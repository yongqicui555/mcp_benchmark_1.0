# Youfiliate MCP Server

<!-- mcp-name: io.github.andrewmpierce/youfiliate-mcp -->

[![PyPI](https://img.shields.io/pypi/v/youfiliate-mcp.svg)](https://pypi.org/project/youfiliate-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/youfiliate-mcp.svg)](https://pypi.org/project/youfiliate-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MCP (Model Context Protocol) server for managing [Youfiliate](https://youfiliate.com) Smart Links from AI assistants like Claude Desktop. Create geo-targeted affiliate links, view analytics, and run YouTube description migrations — all from a chat conversation.

**18 tools, 4 resources, supports stdio + streamable HTTP transports.**

## Installation

```bash
pip install youfiliate-mcp
```

Requires Python 3.11+ and a [Youfiliate](https://youfiliate.com) account.

### Generate an API key

1. Log in at [youfiliate.com](https://youfiliate.com)
2. Go to **Settings → API Keys**
3. Click **Create API Key** (e.g. "Claude Desktop")
4. Copy the key (starts with `youfiliate_sk_`) — shown only once

## Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

### Local (stdio)

```json
{
  "mcpServers": {
    "youfiliate": {
      "command": "youfiliate-mcp",
      "env": {
        "YOUFILIATE_API_KEY": "youfiliate_sk_your_key_here"
      }
    }
  }
}
```

### Remote (Streamable HTTP)

```json
{
  "mcpServers": {
    "youfiliate": {
      "url": "https://mcp.youfiliate.com",
      "headers": {
        "Authorization": "Bearer youfiliate_sk_your_key_here"
      }
    }
  }
}
```

Restart Claude Desktop after editing the config.

## Available Tools (18)

### Smart Links CRUD (5)

| Tool | Description |
|------|-------------|
| `youfiliate_create_smart_link` | Create a new geo-targeted smart link |
| `youfiliate_list_smart_links` | List smart links with filtering and pagination |
| `youfiliate_get_smart_link` | Get full details of a smart link by ID |
| `youfiliate_update_smart_link` | Update a smart link (partial update) |
| `youfiliate_delete_smart_link` | Delete a smart link (requires `confirm=True`) |

### Analytics (3)

| Tool | Description |
|------|-------------|
| `youfiliate_get_smart_link_stats` | Get click analytics for a specific link |
| `youfiliate_get_aggregate_stats` | Get analytics across all links |
| `youfiliate_check_link_health` | Trigger a health check on a link |

### Preferences (2)

| Tool | Description |
|------|-------------|
| `youfiliate_get_preferences` | Get default smart link preferences |
| `youfiliate_update_preferences` | Update preferences for new links |

### YouTube (3)

| Tool | Description |
|------|-------------|
| `youfiliate_get_youtube_status` | Check YouTube connection status |
| `youfiliate_connect_youtube` | Start YouTube OAuth flow (returns auth URL) |
| `youfiliate_disconnect_youtube` | Disconnect YouTube (requires `confirm=True`) |

### Migrations (5)

| Tool | Description |
|------|-------------|
| `youfiliate_preview_migration` | Preview migration scope (dry run) |
| `youfiliate_start_migration` | Start YouTube description migration (requires `confirm=True`) |
| `youfiliate_get_migration_status` | Check migration progress |
| `youfiliate_list_migrations` | List all migrations |
| `youfiliate_rollback_migration` | Rollback a migration (requires `confirm=True`) |

## Available Resources (4)

| URI | Description |
|-----|-------------|
| `youfiliate://summary` | Dashboard summary (link counts, clicks, health) |
| `youfiliate://preferences` | Current preferences (read-only) |
| `youfiliate://smart-link/{id}` | Single smart link details |
| `youfiliate://plan-limits` | Current plan usage and limits |

## Example Conversations

### Creating a Smart Link

> **You:** Create a smart link for `https://amazon.com/dp/B09V3KXJPB` with geo-targeting for UK and Germany.
>
> **Claude:** *(calls `youfiliate_create_smart_link` with geo rules for GB and DE)*
>
> Done. Short URL: `youfil.to/b09v3kxjpb`
> - US (default): amazon.com/dp/B09V3KXJPB
> - UK: amazon.co.uk/dp/B09V3KXJPB
> - Germany: amazon.de/dp/B09V3KXJPB

### Checking Analytics

> **You:** How are my links performing this month?
>
> **Claude:** *(calls `youfiliate_get_aggregate_stats` with `period="30d"`)*
>
> 1,234 clicks. Top countries: US (500), UK (200), Germany (150). Most traffic from YouTube (900 clicks).

### YouTube Migration

> **You:** Convert all my YouTube description links to smart links.
>
> **Claude:** *(calls `youfiliate_preview_migration`)* Would affect 15 videos / 42 links. Proceed?
>
> **You:** Yes.
>
> **Claude:** *(calls `youfiliate_start_migration` with `confirm=True`)*

## Security Model

1. **API key auth.** Your `youfiliate_sk_...` key authenticates the MCP server.
2. **JWT bridge.** The server exchanges your API key for short-lived JWTs against the Youfiliate API.
3. **Token caching.** JWTs are cached in memory and auto-refreshed.
4. **Scoped data access.** The server only sees data belonging to the API key's owner.
5. **Destructive actions guarded.** Delete, disconnect, start migration, and rollback require explicit `confirm=True`.

## Rate Limits

- MCP layer: 60 requests/minute per API key
- Health checks: 1 per link per 5 minutes
- API key exchange: rate-limited by the Youfiliate backend

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `YOUFILIATE_API_KEY` | (required) | Your API key |
| `YOUFILIATE_API_BASE_URL` | `https://app.youfiliate.com` | Backend URL |
| `MCP_SERVER_SECRET` | (empty) | Shared secret for verify-api-key (server operators only) |
| `TRANSPORT` | `stdio` | `stdio` or `streamable-http` |
| `PORT` | `8080` | Port for HTTP transport |
| `HOST` | `127.0.0.1` | Bind address (use `0.0.0.0` in Docker) |

## Development

```bash
git clone https://github.com/andrewmpierce/youfiliate-mcp.git
cd youfiliate-mcp
pip install -e ".[dev]"
pytest -v
```

### Test with MCP Inspector

```bash
npx @modelcontextprotocol/inspector youfiliate-mcp
```

### Docker

```bash
docker build -t youfiliate-mcp .
docker run -p 8080:8080 \
  -e YOUFILIATE_API_KEY=youfiliate_sk_... \
  youfiliate-mcp
```

## Troubleshooting

**"Authentication failed"** — verify your API key, regenerate at [youfiliate.com/settings](https://youfiliate.com/settings) if needed.

**"Could not connect to the Youfiliate API"** — check `YOUFILIATE_API_BASE_URL`. Defaults to `https://app.youfiliate.com`.

**"Rate limit exceeded"** — wait a moment. Health checks are 1 per 5 minutes per link.

**Tools not appearing in Claude Desktop** — check `claude_desktop_config.json` syntax, restart Claude Desktop, run `youfiliate-mcp --help` to verify the binary is on your PATH.

## License

[MIT](LICENSE)

## Links

- Website: [youfiliate.com](https://youfiliate.com)
- Issues: [github.com/andrewmpierce/youfiliate-mcp/issues](https://github.com/andrewmpierce/youfiliate-mcp/issues)
- Changelog: [CHANGELOG.md](CHANGELOG.md)
