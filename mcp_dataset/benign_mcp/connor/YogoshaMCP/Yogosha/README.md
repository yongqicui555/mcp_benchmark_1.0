# Yogosha MCP Server

## Overview
This project provides a seamless bridge between the Yogosha Bug Bounty Platform and the Model Context Protocol (MCP) ecosystem. By exposing all Yogosha API endpoints as MCP tools, it enables security teams, automation engineers, and AI copilots (like Claude Desktop) to interact programmatically with Yogosha resources—without manual API calls or custom scripting.

## Impact
- **Automation:** Instantly automate vulnerability management, asset inventory, reporting, and more using natural language or workflow tools.
- **Integration:** Connect Yogosha with any MCP-compatible agent, LLM, or workflow orchestrator (e.g., Claude Desktop, custom bots).
- **Security:** Enforce API key management via environment variables; no secrets in code. All operations are stateless and auditable.
- **Extensibility:** Add new endpoints or custom logic by simply extending `server.py`—no need to modify core infrastructure.
- **Productivity:** Dramatically reduce the time to triage, update, or report on vulnerabilities and assets.

## What Problems Does This Solve?
- **Manual API Work:** No more writing custom scripts for each Yogosha API call—just use the MCP tool interface.
- **AI Copilot Enablement:** Let LLMs and automation agents manage your bug bounty program, assets, and reports directly.
- **Unified Security Operations:** Integrate Yogosha with other security tools and dashboards using the MCP standard.

## Requirements
- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (for fast Python package management and running)
- Yogosha API Key

## Setup
1. **Install dependencies:**
   ```sh
   uv pip install -r requirements.txt
   ```
2. **Set your Yogosha API key:**
   ```sh
   export YOGOSHA_API_KEY=your_yogosha_api_key_here
   ```
3. **Run the MCP server:**
   ```sh
   uv run server.py
   ```
   The server uses stdio transport by default for integration with Claude Desktop and other MCP clients.

## Quickstart Example
Once running, you can use Claude Desktop or any MCP client to:
- List all programs: `list_programs()`
- Create a new asset: `create_asset(program_id, asset_data)`
- Patch a vulnerability: `patch_vulnerability(program_id, vulnerability_id, patch_data)`

## MCP Server Configuration for Claude Desktop
To use this server with Claude Desktop, add the following to your `mcpserver.json`:

```json
{
  "mcpServers": {
    "YogoshaMCP": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/haji/mcp-servers/yogosha-mcp",
        "run",
        "server.py"
      ]
    }
  }
}
```

- Adjust the `--directory` path if your project is in a different location.
- The server will be available as "YogoshaMCP" in Claude Desktop.

## Security
- The API key is read from the `YOGOSHA_API_KEY` environment variable. **Never commit your API key to source control.**
- All code is designed to be stateless and safe for use as MCP tools.

## Extending
- To add more endpoints, follow the function pattern in `server.py`.

## License
MIT or as specified in this repository.
