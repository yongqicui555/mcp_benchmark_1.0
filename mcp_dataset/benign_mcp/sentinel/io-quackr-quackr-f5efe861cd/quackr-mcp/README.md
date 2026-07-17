# Quackr MCP Server

[![npm version](https://img.shields.io/npm/v/quackr-mcp.svg)](https://www.npmjs.com/package/quackr-mcp)
[![npm downloads](https://img.shields.io/npm/dm/quackr-mcp.svg)](https://www.npmjs.com/package/quackr-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Official MCP server for [Quackr](https://quackr.io) — virtual phone numbers for SMS verification and OTP receipt. Use Claude (or any MCP-compatible client) to check pricing and inventory, purchase temporary numbers, and read incoming SMS programmatically.

- **npm:** [`quackr-mcp`](https://www.npmjs.com/package/quackr-mcp) — `npx -y quackr-mcp`
- **Hosted endpoint:** `https://mcp.quackr.io/`
- **Transport:** Streamable HTTP
- **Auth:** `Authorization: Bearer YOUR_API_KEY` header

## Tools

| Tool | Description |
|---|---|
| `get-balance` | Get the current account balance in USD |
| `get-pricing` | Get phone number rental pricing for a specific country |
| `get-inventory` | Check available phone number inventory for a country |
| `purchase-number` | Purchase a temporary number for receiving SMS (deducts from balance) |
| `check-sms` | Check SMS messages received on a rented number |
| `list-active-numbers` | List all currently active (rented) numbers on the account |

## Getting an API Key

1. Sign in at [quackr.io](https://quackr.io)
2. Open your profile page
3. Copy the API key from the API section

## Install via npm

The [`quackr-mcp`](https://www.npmjs.com/package/quackr-mcp) package is a thin stdio
launcher that bridges any stdio MCP client to the hosted Quackr endpoint. It needs
Node.js 18+ — no separate install required, `npx` fetches it on first run.

```json
{
  "mcpServers": {
    "quackr": {
      "command": "npx",
      "args": ["-y", "quackr-mcp"],
      "env": {
        "QUACKR_API_KEY": "YOUR_API_KEY_HERE"
      }
    }
  }
}
```

You can also pass the key as a flag instead of an env var: `npx -y quackr-mcp --api-key YOUR_API_KEY_HERE`.

## Claude Code Setup

**Remote (recommended)** — connect directly to the hosted endpoint. Add to your
`~/.claude.json` (or a project `.mcp.json`):

```json
{
  "mcpServers": {
    "quackr": {
      "type": "http",
      "url": "https://mcp.quackr.io/",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY_HERE"
      }
    }
  }
}
```

Or via the CLI:

```bash
claude mcp add --transport http quackr https://mcp.quackr.io/ --header "Authorization: Bearer YOUR_API_KEY_HERE"
```

## Claude Desktop Setup

Claude Desktop's JSON config only supports local (stdio) servers. Use the npm
launcher (see [Install via npm](#install-via-npm)) by adding the `npx quackr-mcp`
config above to `claude_desktop_config.json`, then restart Claude Desktop.

Alternatively, add Quackr as a remote connector: **Settings → Connectors → Add
custom connector**, enter `https://mcp.quackr.io/`, and add an `Authorization`
header with the value `Bearer YOUR_API_KEY`.

## Other MCP Clients

Any client supporting remote Streamable HTTP MCP servers with custom headers works. Point it at `https://mcp.quackr.io/` and pass your key via the `Authorization: Bearer YOUR_API_KEY` header.

## REST API

Quackr also exposes a full REST API at `https://api.quackr.io/` — see [`api.quackr.io/swagger.json`](https://api.quackr.io/swagger.json) for the full spec. Same `x-api-key` auth.

## Support

- Website: [quackr.io](https://quackr.io)
- Issues: file in this repo
- Email: support@quackr.io

## License

MIT — see [LICENSE](LICENSE).
