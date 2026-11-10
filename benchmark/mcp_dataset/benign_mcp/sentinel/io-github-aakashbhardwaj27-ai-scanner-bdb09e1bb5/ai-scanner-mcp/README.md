<p align="center">
  <img src="https://raw.githubusercontent.com/Aakashbhardwaj27/ai-scanner/main/logo.svg" width="80" alt="ai-scanner logo">
</p>

<h1 align="center">ai-scanner-mcp</h1>

<p align="center">
  MCP server for ai-scanner - let AI agents scan codebases for LLM usage, AI frameworks, and exposed secrets.
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://nodejs.org/"><img src="https://img.shields.io/badge/node-≥18-brightgreen.svg" alt="Node.js"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-compatible-blue.svg" alt="MCP"></a>
</p>

An [MCP](https://modelcontextprotocol.io) server that exposes [ai-scanner](https://github.com/Aakashbhardwaj27/ai-scanner) as tools for AI agents. Works with Claude Code, Claude Desktop, Cursor, Windsurf, and any MCP-compatible client.

## Tools

| Tool | Description |
|---|---|
| `scan_directory` | Full scan — LLM SDKs, AI frameworks, exposed tokens, and hardcoded secrets with severity levels |
| `check_secrets` | Security check — pass/fail scan for exposed credentials only. Perfect for pre-commit checks |
| `ai_inventory` | AI stack overview — which SDKs, frameworks, models, and API endpoints are used (no secret detection) |

## Setup

### Claude Code

```bash
claude mcp add ai-scanner npx ai-scanner-mcp
```

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ai-scanner": {
      "command": "npx",
      "args": ["ai-scanner-mcp"]
    }
  }
}
```

Config file location:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

### Cursor

Add to `.cursor/mcp.json` in your project:

```json
{
  "mcpServers": {
    "ai-scanner": {
      "command": "npx",
      "args": ["ai-scanner-mcp"]
    }
  }
}
```

### Windsurf

Add to `~/.windsurf/mcp.json`:

```json
{
  "mcpServers": {
    "ai-scanner": {
      "command": "npx",
      "args": ["ai-scanner-mcp"]
    }
  }
}
```

## Example Usage

Once connected, you can ask your AI agent:

- *"Scan this project for any exposed API keys"*
- *"Check if there are any hardcoded secrets before I commit"*
- *"What AI SDKs and frameworks does this codebase use?"*
- *"Run a security scan on ./src and tell me if it's safe to push"*
- *"Give me an AI inventory of this project"*

## Tool Details

### scan_directory

Full scan with all detection categories. Parameters:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `directory` | string | *required* | Path to scan |
| `ai_only` | boolean | `false` | Skip generic secrets (Stripe, GitHub, etc.) |
| `scan_env` | boolean | `false` | Include .env files |
| `include_endpoints` | boolean | `true` | Detect LLM API endpoint URLs |
| `include_models` | boolean | `true` | Detect model name references |

### check_secrets

Security-focused pass/fail check. Parameters:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `directory` | string | *required* | Path to scan |
| `ai_only` | boolean | `false` | Only check AI tokens |
| `scan_env` | boolean | `false` | Include .env files |

### ai_inventory

AI stack awareness (no secret detection). Parameters:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `directory` | string | *required* | Path to scan |

## Detection Coverage

- **AI Tokens (20+)** — OpenAI, Anthropic, Google, AWS, HuggingFace, Groq, Replicate, and more
- **Generic Secrets (59)** — Stripe, Twilio, GitHub, Slack, Discord, database URIs, private keys, JWTs
- **LLM SDKs (23)** — OpenAI, Anthropic, Google Gemini, LiteLLM, AWS Bedrock, and more
- **AI Frameworks (24)** — LangChain, LlamaIndex, CrewAI, AutoGen, DSPy, Vercel AI SDK, and more
- **145 total detection patterns**

## License

[MIT](https://github.com/Aakashbhardwaj27/ai-scanner/blob/main/LICENSE)
