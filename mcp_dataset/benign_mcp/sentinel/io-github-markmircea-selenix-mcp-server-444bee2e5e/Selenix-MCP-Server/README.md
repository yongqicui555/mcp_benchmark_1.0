# Selenix MCP Server

[![npm version](https://img.shields.io/npm/v/@selenix/mcp-server.svg)](https://www.npmjs.com/package/@selenix/mcp-server)

Connect [Claude Desktop](https://claude.ai/download) to [Selenix](https://selenix.io) via the Model Context Protocol. Chat with Claude to create, run, debug, and manage browser automation tests — just like using the built-in AI Assistant, but powered by Claude.

[![Selenix-MCP MCP server](https://glama.ai/mcp/servers/markmircea/Selenix-MCP-Server/badges/card.svg)](https://glama.ai/mcp/servers/markmircea/Selenix-MCP-Server)

## Prerequisites

- [Selenix](https://selenix.io) desktop app installed
- [Claude Desktop](https://claude.ai/download) installed
- [Node.js](https://nodejs.org/) 18 or later

## Enable the Bridge in Selenix

Before using any setup method below, enable the bridge inside Selenix:

1. Open Selenix
2. Go to **System Settings** (gear icon in the sidebar)
3. Scroll to the **MCP Server** section
4. Set **Enable MCP Server** to **Yes**

This starts a local bridge server that the MCP server connects to.

## Setup

Choose one of the following methods:

### Option A: Install via npm (recommended)

```bash
npm install -g @selenix/mcp-server
```

Then find your global npm path:

```bash
npm root -g
```

Open your Claude Desktop config file:

- **Windows**: Press `Win+R`, paste `%APPDATA%\Claude\claude_desktop_config.json`, press Enter
- **macOS**: Open `~/Library/Application Support/Claude/claude_desktop_config.json`

Add the Selenix MCP server, replacing the path with the output from `npm root -g`:

```json
{
  "mcpServers": {
    "selenix": {
      "command": "node",
      "args": ["<npm-root-path>/@selenix/mcp-server/dist/bundle.js"]
    }
  }
}
```

**Example (Windows with nvm):**
```json
{
  "mcpServers": {
    "selenix": {
      "command": "node",
      "args": ["C:/Users/YourName/AppData/Local/nvm/v18.20.8/node_modules/@selenix/mcp-server/dist/bundle.js"]
    }
  }
}
```

**Example (macOS/Linux):**
```json
{
  "mcpServers": {
    "selenix": {
      "command": "node",
      "args": ["/usr/local/lib/node_modules/@selenix/mcp-server/dist/bundle.js"]
    }
  }
}
```

If you already have other MCP servers configured, add `"selenix"` alongside them inside the existing `"mcpServers"` object.

### Option B: Use the bundled version (no npm required)

If you installed Selenix as a desktop app, the MCP server is already bundled. No need to install anything — just point Claude Desktop to the bundled file.

Find your Selenix install folder and look for `resources/mcp-server/index.js`, then add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "selenix": {
      "command": "node",
      "args": ["C:/path/to/Selenix/resources/mcp-server/index.js"]
    }
  }
}
```

**Typical Windows path:**
```
C:/Users/YourName/AppData/Local/Programs/Selenix/resources/mcp-server/index.js
```

### Option C: Manual download

1. Download `bundle.js` from the [npm package page](https://www.npmjs.com/package/@selenix/mcp-server) or from the [releases page](https://github.com/AiBrainOrg/selenix/releases)
2. Save it somewhere on your machine (e.g., `C:/selenix-mcp/bundle.js`)
3. Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "selenix": {
      "command": "node",
      "args": ["C:/selenix-mcp/bundle.js"]
    }
  }
}
```

Node.js is still required — the MCP server is a single JavaScript file with no other dependencies.

## Verify

Restart Claude Desktop after editing the config. You should see the Selenix tools icon (hammer) in the chat input area.

Try asking Claude:

- "What tests are in my Selenix project?"
- "Create a test that opens google.com and searches for 'selenium automation'"
- "Run the current test and fix any failures"
- "Take a screenshot of the browser"

## How It Works

```
Claude Desktop <--stdio--> MCP Server <--HTTP--> Bridge Server (inside Selenix)
```

The MCP server translates Claude's tool calls into HTTP requests to a bridge server running inside Selenix. The bridge has full access to Selenix internals — the same capabilities as the built-in AI Assistant.

- The bridge only listens on `127.0.0.1` (localhost) — no network exposure
- Auth is handled via a bearer token auto-generated each time Selenix starts
- Connection config is stored at `~/.selenix/bridge.json` and re-read on every call, so restarting Selenix does not require restarting Claude Desktop

## Available Tools

### Reading & Inspection

| Tool | Description |
|------|-------------|
| `get_screenshot` | Capture a screenshot of the browser window |
| `get_page_html` | Get the page HTML with interactive elements annotated |
| `get_search_html` | Search page HTML by regex pattern |
| `get_selected_command_info` | Get DOM context for a command's target element |
| `get_current_test` | Get all commands in the current test |
| `get_test_list` | List all tests in the project |
| `get_test_by_name` | Get a test by its name |
| `get_command_list` | List all available Selenix commands |
| `get_command_info` | Get detailed docs for a specific command |
| `get_project_info` | Get project metadata |
| `get_active_suite` | Get the active test suite |
| `get_step_results` | Get pass/fail results from the last test run |
| `get_logs` | Get recent logs (all types), 20 per page, most recent first. Optional `page` param for pagination. |
| `get_workspace_context` | Get a summary of the current workspace |

### Writing & Execution

| Tool | Description |
|------|-------------|
| `add_commands` | Add commands to a test at a specific position |
| `run_test` | Run a test and wait for results (up to 2 minutes) |
| `clear_and_replace_commands` | Replace all commands in a test |
| `fix_commands` | Apply targeted fixes — update, remove, or insert commands |

## Troubleshooting

**"Cannot read Selenix bridge config"**
Selenix isn't running or the MCP Server isn't enabled. Open Selenix → System Settings → set Enable MCP Server to Yes.

**"Cannot connect to Selenix bridge"**
Selenix may have just restarted. Try the request again — the MCP server will automatically pick up the new connection details.

**Tools not appearing in Claude Desktop**
Make sure you restarted Claude Desktop after editing the config file. Verify the config JSON is valid (no trailing commas, correct brackets).

**Claude Desktop won't open after config change**
The config JSON is likely malformed. Open the config file in a text editor, fix the JSON syntax, and try again. Common issues: missing comma between entries, trailing comma after the last entry.

## Uninstall

```bash
npm uninstall -g @selenix/mcp-server
```

Then remove the `"selenix"` entry from your Claude Desktop config file and restart Claude Desktop.