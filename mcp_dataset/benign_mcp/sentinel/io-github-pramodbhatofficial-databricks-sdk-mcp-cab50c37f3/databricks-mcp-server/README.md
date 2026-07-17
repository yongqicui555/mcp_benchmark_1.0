# Databricks MCP Server

<!-- mcp-name: io.github.pramodbhatofficial/databricks-sdk-mcp -->

[![PyPI](https://img.shields.io/pypi/v/databricks-sdk-mcp.svg)](https://pypi.org/project/databricks-sdk-mcp/)
[![CI](https://github.com/pramodbhatofficial/databricks-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/pramodbhatofficial/databricks-mcp-server/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

A comprehensive [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for Databricks, built on the official [Databricks Python SDK](https://github.com/databricks/databricks-sdk-py).

Provides **263 tools** and **8 prompt templates** across 28 service domains, giving AI assistants full access to the Databricks platform.

## Features

- **SDK-first**: Uses `databricks-sdk` for type safety and automatic API freshness
- **Comprehensive**: Covers Unity Catalog, SQL, Compute, Jobs, Pipelines, Serving, Vector Search, Apps, Lakebase, Dashboards, Genie, Secrets, IAM, Connections, Experiments, and Delta Sharing
- **Zero custom auth**: Delegates authentication entirely to the SDK (PAT, OAuth, Azure AD, service principal -- all automatic)
- **Selective loading**: Include/exclude tool modules via environment variables
- **MCP Resources**: Read-only workspace context (URL, current user, auth type)

## Quick Start

### Installation

```bash
pip install databricks-sdk-mcp
```

Or run with Docker:

```bash
docker run -i -e DATABRICKS_HOST=... -e DATABRICKS_TOKEN=... databricks-mcp
```

Or install from source:

```bash
git clone https://github.com/pramodbhatofficial/databricks-mcp-server.git
cd databricks-mcp-server
pip install -e ".[dev]"
```

### Authentication

Authentication is handled by the Databricks SDK. Set one of:

**Personal Access Token (simplest):**

```bash
export DATABRICKS_HOST=https://your-workspace.databricks.com
export DATABRICKS_TOKEN=dapi...
```

**OAuth (M2M):**

```bash
export DATABRICKS_HOST=https://your-workspace.databricks.com
export DATABRICKS_CLIENT_ID=...
export DATABRICKS_CLIENT_SECRET=...
```

**Other methods**: Azure AD, Databricks CLI profile, Azure Managed Identity -- all auto-detected by the SDK.

### Running

```bash
databricks-mcp
```

This starts the MCP server using stdio transport.

## Integrations

### Claude Code (Terminal)

Add to `~/.claude/settings.json` or your project's `.claude/settings.json`:

```json
{
  "mcpServers": {
    "databricks": {
      "command": "databricks-mcp",
      "env": {
        "DATABRICKS_HOST": "https://your-workspace.databricks.com",
        "DATABRICKS_TOKEN": "dapi..."
      }
    }
  }
}
```

Then restart Claude Code. Verify with `/mcp` to see the registered tools.

### Claude Desktop

Add to your Claude Desktop config file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "databricks": {
      "command": "databricks-mcp",
      "env": {
        "DATABRICKS_HOST": "https://your-workspace.databricks.com",
        "DATABRICKS_TOKEN": "dapi..."
      }
    }
  }
}
```

Restart Claude Desktop. The Databricks tools will appear in the tool picker.

### Cursor

Add to `.cursor/mcp.json` in your project root (or `~/.cursor/mcp.json` for global):

```json
{
  "mcpServers": {
    "databricks": {
      "command": "databricks-mcp",
      "env": {
        "DATABRICKS_HOST": "https://your-workspace.databricks.com",
        "DATABRICKS_TOKEN": "dapi..."
      }
    }
  }
}
```

Open Cursor Settings > MCP to verify the server is connected.

### Windsurf

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "databricks": {
      "command": "databricks-mcp",
      "env": {
        "DATABRICKS_HOST": "https://your-workspace.databricks.com",
        "DATABRICKS_TOKEN": "dapi..."
      }
    }
  }
}
```

### VS Code (Copilot)

Add to `.vscode/mcp.json` in your project:

```json
{
  "servers": {
    "databricks": {
      "command": "databricks-mcp",
      "env": {
        "DATABRICKS_HOST": "https://your-workspace.databricks.com",
        "DATABRICKS_TOKEN": "dapi..."
      }
    }
  }
}
```

### Zed

Add to Zed's settings (`~/.config/zed/settings.json`):

```json
{
  "context_servers": {
    "databricks": {
      "command": {
        "path": "databricks-mcp",
        "env": {
          "DATABRICKS_HOST": "https://your-workspace.databricks.com",
          "DATABRICKS_TOKEN": "dapi..."
        }
      }
    }
  }
}
```

### Any MCP Client (Generic stdio)

The server uses stdio transport. Connect from any MCP-compatible client:

```bash
# Set auth env vars
export DATABRICKS_HOST=https://your-workspace.databricks.com
export DATABRICKS_TOKEN=dapi...

# Start the server (communicates via stdin/stdout)
databricks-mcp
```

### Tip: Load Only What You Need

If your MCP client struggles with many tools, use selective loading to reduce the tool count:

```json
{
  "mcpServers": {
    "databricks": {
      "command": "databricks-mcp",
      "env": {
        "DATABRICKS_HOST": "https://your-workspace.databricks.com",
        "DATABRICKS_TOKEN": "dapi...",
        "DATABRICKS_MCP_TOOLS_INCLUDE": "unity_catalog,sql,compute,jobs"
      }
    }
  }
}
```

## Tool Modules

| Module | Tools | Description |
|--------|-------|-------------|
| `unity_catalog` | 23 | Catalogs, schemas, tables, volumes, functions, registered models |
| `sql` | 14 | Warehouses, SQL execution, queries, alerts, history |
| `workspace` | 10 | Notebooks, files, repos |
| `compute` | 18 | Clusters, instance pools, policies, node types, Spark versions |
| `jobs` | 13 | Jobs, runs, tasks, repair, cancel all |
| `pipelines` | 8 | DLT / Lakeflow pipelines |
| `serving` | 10 | Serving endpoints, model versions, OpenAPI |
| `vector_search` | 10 | Vector search endpoints, indexes, sync |
| `apps` | 10 | Databricks Apps lifecycle |
| `database` | 10 | Lakebase PostgreSQL instances |
| `dashboards` | 9 | Lakeview AI/BI dashboards, published views |
| `genie` | 5 | Genie AI/BI conversations |
| `secrets` | 8 | Secret scopes and secrets |
| `iam` | 16 | Users, groups, service principals, permissions, current user |
| `connections` | 5 | External connections |
| `experiments` | 14 | MLflow experiments, runs, artifacts, metrics, params |
| `sharing` | 11 | Delta Sharing shares, recipients, providers |
| `files` | 12 | DBFS and UC Volumes file operations |
| `grants` | 3 | Unity Catalog permission grants (GRANT/REVOKE) |
| `storage` | 10 | Storage credentials and external locations |
| `metastores` | 8 | Unity Catalog metastore management |
| `online_tables` | 3 | Online tables for low-latency serving |
| `global_init_scripts` | 5 | Workspace-wide init scripts |
| `tokens` | 5 | Personal access token management |
| `git_credentials` | 5 | Git credential management for repos |
| `quality_monitors` | 8 | Data quality monitoring and refreshes |
| `command_execution` | 4 | Interactive command execution on clusters |
| `workflows` | 5 | Composite multi-step operations (workspace status, schema setup, query preview) |

## Selective Tool Loading

With 263 tools, it's recommended to load only the modules you need. This improves agent performance and tool selection accuracy.

### Role-Based Presets (Recommended)

Pick a preset that matches your role:

| Preset | Modules | Tools | Config |
|--------|---------|-------|--------|
| **Data Engineer** | unity_catalog, sql, compute, jobs, pipelines, files, quality_monitors | ~100 | `DATABRICKS_MCP_TOOLS_INCLUDE=unity_catalog,sql,compute,jobs,pipelines,files,quality_monitors` |
| **ML Engineer** | serving, vector_search, experiments, compute, unity_catalog, online_tables, files | ~98 | `DATABRICKS_MCP_TOOLS_INCLUDE=serving,vector_search,experiments,compute,unity_catalog,online_tables,files` |
| **Platform Admin** | iam, secrets, tokens, metastores, compute, global_init_scripts, grants, storage | ~85 | `DATABRICKS_MCP_TOOLS_INCLUDE=iam,secrets,tokens,metastores,compute,global_init_scripts,grants,storage` |
| **App Developer** | apps, database, sql, files, serving, secrets | ~64 | `DATABRICKS_MCP_TOOLS_INCLUDE=apps,database,sql,files,serving,secrets` |
| **Data Analyst** | sql, unity_catalog, dashboards, genie, workspace | ~61 | `DATABRICKS_MCP_TOOLS_INCLUDE=sql,unity_catalog,dashboards,genie,workspace` |
| **Minimal** | sql, unity_catalog | ~37 | `DATABRICKS_MCP_TOOLS_INCLUDE=sql,unity_catalog` |

Example using a preset in Claude Code:

```json
{
  "mcpServers": {
    "databricks": {
      "command": "databricks-mcp",
      "env": {
        "DATABRICKS_HOST": "https://your-workspace.databricks.com",
        "DATABRICKS_TOKEN": "dapi...",
        "DATABRICKS_MCP_TOOLS_INCLUDE": "unity_catalog,sql,compute,jobs,pipelines,files,quality_monitors"
      }
    }
  }
}
```

### Custom Filtering

```bash
# Only include specific modules
export DATABRICKS_MCP_TOOLS_INCLUDE=unity_catalog,sql,serving

# Exclude specific modules (cannot combine with INCLUDE)
export DATABRICKS_MCP_TOOLS_EXCLUDE=iam,sharing,experiments
```

If `INCLUDE` is set, only those modules load. If `EXCLUDE` is set, everything except those modules loads. `INCLUDE` takes precedence if both are set.

## Tool Discovery (For AI Agents)

The server includes built-in tool discovery to help AI agents find the right tools:

### MCP Resources

| URI | Description |
|-----|-------------|
| `databricks://workspace/info` | Workspace URL, current user, auth type |
| `databricks://tools/guide` | Tool catalog with module descriptions, use cases, and role presets |

Agents can read `databricks://tools/guide` at connection time to understand what's available.

### Discovery Tool

The `databricks_tool_guide` tool helps agents find the right tools during a conversation:

```
# Find tools for a specific task
databricks_tool_guide(task="run a SQL query")
databricks_tool_guide(task="deploy an ML model")
databricks_tool_guide(task="create a user")

# Get role-based recommendations
databricks_tool_guide(role="data_engineer")
databricks_tool_guide(role="ml_engineer")
```

This returns matching modules with descriptions and usage hints, so the agent knows exactly which `databricks_*` tools to call.

## MCP Prompts (Guided Workflows)

The server includes 8 prompt templates that guide AI agents through multi-step Databricks workflows:

| Prompt | Description |
|--------|-------------|
| `explore_data_catalog` | Browse Unity Catalog structure (catalogs → schemas → tables) |
| `query_data` | Find a warehouse, execute SQL, and format results |
| `debug_failing_job` | Investigate a failing job: status, logs, error analysis |
| `setup_ml_experiment` | Create an MLflow experiment and configure tracking |
| `deploy_model` | Deploy a model to a serving endpoint |
| `setup_data_pipeline` | Create a DLT pipeline with scheduling |
| `workspace_health_check` | Audit clusters, warehouses, jobs, and endpoints |
| `manage_permissions` | Review and update permissions on workspace objects |

Prompts appear automatically in MCP clients that support them (e.g., Claude Desktop's prompt picker).

## Docker

Run the MCP server in a container:

```bash
# Build
docker build -t databricks-mcp .

# Run with stdio
docker run -i \
  -e DATABRICKS_HOST=https://your-workspace.databricks.com \
  -e DATABRICKS_TOKEN=dapi... \
  databricks-mcp

# Run with SSE transport
docker run -p 8080:8080 \
  -e DATABRICKS_HOST=https://your-workspace.databricks.com \
  -e DATABRICKS_TOKEN=dapi... \
  databricks-mcp --transport sse --port 8080

# Run with selective modules
docker run -i \
  -e DATABRICKS_HOST=https://your-workspace.databricks.com \
  -e DATABRICKS_TOKEN=dapi... \
  -e DATABRICKS_MCP_TOOLS_INCLUDE=sql,unity_catalog \
  databricks-mcp
```

## SSE Transport (Remote Server)

The server supports SSE transport for remote connections:

```bash
# Start as SSE server
databricks-mcp --transport sse --port 8080

# Custom host/port
databricks-mcp --transport sse --host 127.0.0.1 --port 3000
```

Connect from any MCP client that supports SSE:

```json
{
  "mcpServers": {
    "databricks": {
      "url": "http://localhost:8080/sse"
    }
  }
}
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Lint
ruff check databricks_mcp/

# Test
pytest tests/ -v
```

## Author

**Pramod Bhat**

## License

Apache 2.0 -- see [LICENSE](LICENSE).
