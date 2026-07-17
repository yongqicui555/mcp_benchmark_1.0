# Connecting to the Halal Terminal MCP server

## Endpoint

```
https://mcp.halalterminal.com/sse
```

- Transport: **SSE** (Server-Sent Events)
- Auth: `X-API-Key: <your_key>` header, or `?api_key=<your_key>` query param
- Get a key (free, no credit card): https://api.halalterminal.com

---

## Claude Code

### Option A — direct SSE (recommended)

```bash
claude mcp add --transport sse halalterminal \
  https://mcp.halalterminal.com/sse \
  --header "X-API-Key: ht_yourkey"
```

### Option B — project-scoped via `.mcp.json`

```json
{
  "mcpServers": {
    "halalterminal": {
      "type": "sse",
      "url": "https://mcp.halalterminal.com/sse",
      "headers": { "X-API-Key": "ht_yourkey" }
    }
  }
}
```

> Prefer the [`halalterminal-claude-skills`](https://github.com/goww7/halalterminal-claude-skills) plugin — it ships a `/halal-setup` slash command that handles this for you.

---

## Claude Desktop

Edit `claude_desktop_config.json` (Settings → Developer → Edit Config) and add the entry below. Claude Desktop currently expects stdio, so we use the official `@halalterminal/mcp` package as a stdio↔SSE bridge.

```json
{
  "mcpServers": {
    "halalterminal": {
      "command": "npx",
      "args": ["-y", "@halalterminal/mcp"],
      "env": { "HALALTERMINAL_API_KEY": "ht_yourkey" }
    }
  }
}
```

Prefer a generic bridge? Both of these work too:

```json
{ "command": "npx", "args": ["-y", "supergateway", "--sse", "https://mcp.halalterminal.com/sse", "--header", "X-API-Key:ht_yourkey"] }
```

```json
{ "command": "npx", "args": ["-y", "mcp-proxy", "--sse-url", "https://mcp.halalterminal.com/sse", "--header", "X-API-Key=ht_yourkey"] }
```

---

## Cursor

Cursor → Settings → MCP → *New MCP server*:

```json
{
  "mcpServers": {
    "halalterminal": {
      "url": "https://mcp.halalterminal.com/sse?api_key=ht_yourkey"
    }
  }
}
```

---

## Windsurf

Windsurf → Settings → Cascade → MCP servers:

```json
{
  "mcpServers": {
    "halalterminal": {
      "serverUrl": "https://mcp.halalterminal.com/sse",
      "headers": { "X-API-Key": "ht_yourkey" }
    }
  }
}
```

---

## Stdio-only clients

For any MCP client that requires stdio, the `@halalterminal/mcp` package IS the bridge — point the client at it:

```json
{
  "mcpServers": {
    "halalterminal": {
      "command": "npx",
      "args": ["-y", "@halalterminal/mcp"],
      "env": { "HALALTERMINAL_API_KEY": "ht_yourkey" }
    }
  }
}
```

Source: https://github.com/goww7/halalterminal-mcp/blob/main/bin/cli.mjs (Apache-2.0, ~50 lines).

---

## Verifying the connection

After connecting, ask your assistant:

> *"List the available halalterminal tools."*

You should see all 22 tools. Then try:

> *"Is AAPL halal?"*

If the call fails with `401`, the API key is missing or invalid. `403` means the key was deactivated. Check https://halalterminal.com/dashboard.

---

## Authentication details

| Method | Where |
|---|---|
| Header | `X-API-Key: ht_...` |
| Query string | `?api_key=ht_...` |

The server validates each request against the Halal Terminal API-key registry. The owning key is propagated to every tool call so per-user data (watchlists, screening cache) is correctly scoped.

## Plans

| Plan | Tokens / month | Price |
|---|---|---|
| Free | 50 | $0 |
| Starter | 2,500 | $19 |
| Pro | 15,000 | $49 |
| Enterprise | Unlimited | $199+ |

Upgrade: https://halalterminal.com/pricing
