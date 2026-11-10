# Bugcrowd MCP Server

This project provides a Model Context Protocol (MCP) server that exposes the entire [Bugcrowd REST API](https://docs.bugcrowd.com/api/2025-04-23/) as callable tools for LLMs and automation. It is implemented in Python using the async MCP SDK and is ready to be used with Claude Desktop, MCP Inspector, or any compatible LLM agent.

## Description

**Bugcrowd MCP Server** acts as a bridge between LLMs (like Claude, GPT, etc.) and the Bugcrowd platform. It exposes every Bugcrowd API endpoint as a tool, allowing you to:
- Query programs, submissions, reports, assets, users, and more
- Create, update, or delete resources on Bugcrowd
- Automate vulnerability management and reporting
- Integrate Bugcrowd data into your own workflows, dashboards, or security automations

All API calls are made securely and asynchronously, and credentials are never hardcoded.

## Features
- **Full Bugcrowd API Coverage:** All documented endpoints are available as MCP tools (GET, POST, PATCH, DELETE, etc.).
- **Async & Scalable:** Built with async Python and `httpx` for high concurrency and responsiveness.
- **Secure:** Credentials are read from environment variables and never hardcoded.
- **Easy Integration:** Ready to use with Claude Desktop or any MCP-compatible client.

## Usage

### 1. Install dependencies
This project uses [uv](https://github.com/astral-sh/uv) for fast Python dependency management:

```sh
uv pip install -r requirements.txt
```

Or, if you use `pyproject.toml`:

```sh
uv pip install .
```

### 2. Set your Bugcrowd API credentials
Export your Bugcrowd API username and password as environment variables:

```sh
export BUGCROWD_API_USERNAME="your_username"
export BUGCROWD_API_PASSWORD="your_password"
```

> **Note:** The server will start and show all available tools even if these environment variables are not set. However, any attempt to call a Bugcrowd API tool will result in a runtime error until the credentials are provided.

### 3. Run the MCP server

This server uses **stdio transport** by default (no HTTP server is started). This is the recommended mode for Claude Desktop and most LLM integrations.

```sh
uv run server.py
```

### 4. Configure in Claude Desktop
Add the following to your Claude Desktop `mcpserver.json` configuration (adjust the directory path as needed):

```json
{
  "mcpServers": {
    "BugcrowdMCP": {
      "command": "uv",
      "args": [
        "--directory", "/Users/haji/mcp-servers/bugcrowd-mcp",
        "run", "server.py"
      ]
    }
  }
}
```

> **Note:** No HTTP server is started; all communication is via stdio (standard input/output) for maximum compatibility and security with LLM tools.

### 5. Example: Calling a Tool
Once the server is running and connected to your LLM or MCP client, you can call any Bugcrowd API endpoint as a tool. For example, to list all programs:

**Prompt to LLM or MCP client:**
```
Call the tool `get_programs` to list all Bugcrowd programs I have access to.
```

**Example tool call (pseudo-code):**
```python
# Using an MCP client or LLM agent
result = call_tool("get_programs", {})
print(result)
```

You can also pass query parameters as needed:
```python
result = call_tool("get_programs", {"fields[program]": "name,code"})
```

To get a specific program by ID:
```python
result = call_tool("get_program", {"id": "PROGRAM_UUID"})
```

To create a new report:
```python
result = call_tool("post_reports", {"data": {"type": "report", "attributes": {"title": "Test Report", "description": "Example."}}})
```

### 6. Impact
- **LLMs and agents** can now interact with the full Bugcrowd API securely and programmatically, enabling automation, reporting, and integration with other tools.
- **Security teams** can automate vulnerability management, reporting, and data extraction from Bugcrowd.
- **Developers** can rapidly prototype workflows that leverage Bugcrowd data and actions, all from a single, standardized MCP interface.

## Project Structure
- `server.py` — The main MCP server exposing Bugcrowd API endpoints as tools.
- `README.md` — This documentation.
- `pyproject.toml` — Project dependencies.

## Requirements
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (for running and dependency management)
- [httpx](https://www.python-httpx.org/) (for async HTTP requests)
- [mcp](https://github.com/modelcontextprotocol/python-sdk) (MCP Python SDK)

## License
MIT
