# Install And Connect

AI Business System Advisor MCP can be used as a local stdio MCP server or as a remote Streamable HTTP MCP server.

## Local Stdio

Use this command in MCP clients that support stdio servers:

```json
{
  "mcpServers": {
    "ai-business-system-advisor": {
      "command": "npx",
      "args": ["-y", "ai-business-system-advisor-mcp"]
    }
  }
}
```

You can also run the server directly:

```bash
npx -y ai-business-system-advisor-mcp
```

## Remote MCP

Use this remote MCP URL in clients that support Streamable HTTP:

```text
https://mcp.prodxsolution.com/ai-business-system-advisor/mcp
```

## Good First Questions

- Which workflow should I automate first?
- Is this AI agent idea safe for my customer experience?
- Where should humans stay in control?
- What information is missing before implementation?
