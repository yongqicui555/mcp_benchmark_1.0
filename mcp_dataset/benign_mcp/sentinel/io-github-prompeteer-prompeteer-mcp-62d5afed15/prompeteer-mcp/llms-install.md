# Installing Prompeteer MCP Server

Prompeteer is a remote MCP server — no local installation or dependencies required.

## Quick Setup

**Server URL (SSE):** `https://prompeteer.ai/mcp/sse`
**Server URL (Streamable HTTP):** `https://prompeteer.ai/mcp`
**Authentication:** OAuth 2.1 (automatic login redirect)

Add the server URL to your MCP client. You'll be redirected to sign in with your Prompeteer account.

## Available Tools

| Tool | Description | Type |
|------|-------------|------|
| `generate_prompt` | Generate expert-level AI prompts for 140+ platforms | Write |
| `list_prompts` | Browse your PromptDrive library with search and filtering | Read |
| `get_prompt` | Retrieve a specific saved prompt by ID | Read |
| `score_prompt` | Analyze prompt quality across 16 dimensions | Read |
| `save_to_promptdrive` | Save prompts to your PromptDrive library | Write |

## Client Configuration

### Claude Desktop
```json
{
  "mcpServers": {
    "prompeteer": {
      "url": "https://prompeteer.ai/mcp/sse",
      "transport": "sse"
    }
  }
}
```

### Cursor
```json
{
  "servers": {
    "prompeteer": {
      "type": "sse",
      "url": "https://prompeteer.ai/mcp/sse"
    }
  }
}
```

### VS Code / GitHub Copilot
```json
{
  "servers": {
    "prompeteer": {
      "type": "sse",
      "url": "https://prompeteer.ai/mcp/sse"
    }
  }
}
```

## Pricing

- **Free:** 5 prompt generations/month
- **Pro ($50/mo):** Unlimited generations
- All read-only tools are free and unlimited

## Links

- Website: https://prompeteer.ai
- Privacy Policy: https://prompeteer.ai/privacy
- Terms of Service: https://prompeteer.ai/terms
- Support: info@prompeteer.com
