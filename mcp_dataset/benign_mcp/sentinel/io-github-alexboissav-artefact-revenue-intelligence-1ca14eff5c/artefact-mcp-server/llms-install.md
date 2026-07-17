# Installing Artefact Revenue Intelligence MCP Server

## Prerequisites
- Python 3.10+
- Optional: HubSpot private app access token (tools work with demo data without it)

## Install

```bash
pip install artefact-mcp
```

Or run directly with uvx (no install needed):

```bash
uvx artefact-mcp
```

**Note:** For MCP server configuration (Claude Desktop, Cursor, etc.), we recommend using the Python method (`python3 -m artefact_mcp`) instead of `uvx` to avoid PATH issues. See configuration sections below.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `HUBSPOT_API_KEY` | No | HubSpot private app token (format: `pat-na1-xxxxxxxx`). Without it, use `source="sample"` for demo data. |
| `ARTEFACT_LICENSE_KEY` | No | License key for Pro/Enterprise tier. Free tier (sample data) works without a key. |

## Claude Desktop Configuration

Add to `claude_desktop_config.json`:

**Recommended (Python method):**
```json
{
  "mcpServers": {
    "artefact-revenue": {
      "command": "python3",
      "args": ["-m", "artefact_mcp"],
      "env": {
        "HUBSPOT_API_KEY": "pat-na1-xxxxxxxx"
      }
    }
  }
}
```

**Alternative (uvx method):**
```json
{
  "mcpServers": {
    "artefact-revenue": {
      "command": "uvx",
      "args": ["artefact-mcp"],
      "env": {
        "HUBSPOT_API_KEY": "pat-na1-xxxxxxxx"
      }
    }
  }
}
```

*Note: If using uvx and seeing "Server disconnected" errors, see [Common Issues](#common-issues) below.*

## Claude Code Configuration

```bash
claude mcp add artefact-revenue -- uvx artefact-mcp
```

Or with environment variable:

```bash
claude mcp add artefact-revenue -e HUBSPOT_API_KEY=pat-na1-xxxxxxxx -- uvx artefact-mcp
```

## Cursor Configuration

Add to `.cursor/mcp.json`:

**Recommended (Python method):**
```json
{
  "mcpServers": {
    "artefact-revenue": {
      "command": "python3",
      "args": ["-m", "artefact_mcp"],
      "env": {
        "HUBSPOT_API_KEY": "pat-na1-xxxxxxxx"
      }
    }
  }
}
```

**Alternative (uvx method):**
```json
{
  "mcpServers": {
    "artefact-revenue": {
      "command": "uvx",
      "args": ["artefact-mcp"],
      "env": {
        "HUBSPOT_API_KEY": "pat-na1-xxxxxxxx"
      }
    }
  }
}
```

## Windsurf Configuration

Add to Windsurf MCP settings with the same structure as Cursor.

## Available Tools After Installation

| Tool | Description |
|------|-------------|
| `run_rfm` | Run RFM analysis — scores clients on Recency, Frequency, Monetary value, segments into 11 categories |
| `qualify` | Score a prospect against the 14.5-point ICP model — returns tier and engagement strategy |
| `score_pipeline_health` | Analyze pipeline health — velocity, conversion rates, at-risk deals, 0-100 health score |

## Available Resources

| URI | Description |
|-----|-------------|
| `methodology://scoring-model` | 14.5-point ICP scoring model reference |
| `methodology://tier-definitions` | 4-tier classification (Ideal / Strong / Moderate / Poor) |
| `methodology://rfm-segments` | 11 RFM segment definitions with scoring scales |
| `methodology://spiced-framework` | SPICED discovery framework reference |

## Verify Installation

Ask your AI assistant:
- "Run an RFM analysis with sample data"
- "Qualify a SaaS company with $5M revenue and 80 employees in Ontario"
- "Score pipeline health using sample data"

## Common Issues

### Server Disconnected (uvx PATH Issue)

**Problem:** "MCP artefact-revenue: Server disconnected" error when using `uvx` command.

**Cause:** Claude Desktop and other sandboxed applications may not have access to `uvx` in your PATH. This commonly happens when `uvx` is installed via:
- Homebrew → `~/.local/bin/uvx`
- curl installation → `~/.cargo/bin/uvx`

**Solutions:**

1. **Switch to Python method (recommended):**
   ```json
   {
     "mcpServers": {
       "artefact-revenue": {
         "command": "python3",
         "args": ["-m", "artefact_mcp"],
         "env": {}
       }
     }
   }
   ```

2. **Use full uvx path:** Find your uvx location and use the full path:
   ```bash
   which uvx
   # Example output: /Users/yourname/.local/bin/uvx
   ```

   Update config:
   ```json
   {
     "mcpServers": {
       "artefact-revenue": {
         "command": "/Users/yourname/.local/bin/uvx",
         "args": ["artefact-mcp"],
         "env": {}
       }
     }
   }
   ```

3. **Verify manually:** Test that the server starts:
   ```bash
   uvx artefact-mcp==0.2.3
   # Should see: "Artefact Revenue Intelligence MCP Server running..."
   ```

### Other Issues

- **"HubSpot API key required"** — Set `HUBSPOT_API_KEY` or use `source="sample"` for demo data
- **"Pro license required"** — Live HubSpot data requires a license. Use `source="sample"` for free demo data
- **Import errors with `python3 -m artefact_mcp`** — Ensure package is installed: `pip install artefact-mcp`
- **Server won't start** — Ensure Python 3.10+ and `fastmcp>=2.0` are installed
