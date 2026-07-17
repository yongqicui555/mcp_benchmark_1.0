# canvas-mcp

<!-- mcp-name: io.github.admin978/canvas-mcp -->

Local-first MCP server for Canvas LMS. Stdio transport, no network round-trips beyond the official Canvas API.

> **Status:** alpha. Single-user, no warranty, API surface may still shift. File issues if it breaks.

## Why

Canvas is built for instructors. As a student you get a fragmented UI, no cross-course search, and notifications that arrive late or never. This server exposes the Canvas REST API as MCP tools so you can drive the LMS from any MCP-compatible client (Claude Code, Claude Desktop, etc.).

## Architecture

```
[client] ──stdio──> [server.py] ──https──> [Canvas API]
```

- Token lives in `~/.canvas.env` (`chmod 600`)
- Server runs locally, no third party in the path
- Single file, fully auditable

## Tools exposed

`list_courses`, `list_assignments`, `list_modules`, `list_announcements`, `get_page`, `get_file_info`, `get_grades`, `planner_items`, `upcoming_events`, `todo`.

## Setup

### 1. Mint a Canvas personal access token

In Canvas: **Account → Settings → Approved Integrations → + New Access Token**. Copy the token shown — it is not retrievable afterwards.

### 2. Install

From PyPI (recommended):
```bash
pip install canvas-local-mcp
```

Or from source:
```bash
git clone https://github.com/admin978/canvas-mcp.git && cd canvas-mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

Then create the env file:
```bash
curl -fsSL https://raw.githubusercontent.com/admin978/canvas-mcp/main/.canvas.env.example -o ~/.canvas.env
chmod 600 ~/.canvas.env
# edit ~/.canvas.env: set CANVAS_BASE_URL (institution root, no /api/v1)
# and paste the token into CANVAS_TOKEN
```

### 3. Register with your MCP client

Claude Code:
```bash
claude mcp add canvas-local -- canvas-local-mcp
```

Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "canvas-local": {
      "command": "canvas-local-mcp"
    }
  }
}
```

## Bulk dump

`canvas-local-mcp-dump` downloads every file the user has access to (course materials, syllabi). Useful for offline indexing.

```bash
canvas-local-mcp-dump              # all active courses
canvas-local-mcp-dump 12345 67890  # specific course IDs
```

Output goes to `./canvas-dump/` by default. Override with `CANVAS_DUMP_DIR=/path/to/dir`.

## License

MIT — see `LICENSE`.

---

Built by [AGENTE 404 S.L.](https://www.agente404.com) · admin@agente404.com
