# selectic-mcp

MCP connector for [Selectic](https://selectic.ai) — give your AI assistant (Claude, ChatGPT, Perplexity, or any MCP-compatible app) the ability to **call, text, and email businesses** for you: get quotes, book appointments, ask questions — and read back the transcript, recording, and replies. New accounts start with **$2 free**. US businesses for now.

Most apps can add the hosted endpoint directly as a custom connector:

```
https://selectic.ai/api/mcp
```

You'll be prompted to **sign in (OAuth)** the first time — no API key to manage. For stdio-only clients (e.g. Claude Desktop), this package bridges stdio ↔ the hosted endpoint.

## Use

```bash
npx -y @selectic/mcp@latest
```

It opens a browser the first time so you can sign in to Selectic.

Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "selectic": {
      "command": "npx",
      "args": ["-y", "@selectic/mcp@latest"]
    }
  }
}
```

## Tools
`place_call`, `get_call`, `send_sms`, `send_email`, `get_replies`, `list_outreach`, `list_call_types`. See https://selectic.ai/docs.
