# MigratorXpress MCP Server

<!-- mcp-name: io.github.arpe-io/migratorxpress-mcp -->

[![PyPI](https://img.shields.io/pypi/v/migratorxpress-mcp)](https://pypi.org/project/migratorxpress-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Registry](https://img.shields.io/badge/MCP-Registry-blue)](https://registry.modelcontextprotocol.io/?q=arpe-io)

A [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server for [MigratorXpress](https://aetperf.github.io/MigratorXpress-Documentation/), enabling database migration between heterogeneous database systems through AI assistants.

MigratorXpress supports migrating from Oracle, PostgreSQL, SQL Server, and Netezza to PostgreSQL or SQL Server targets.

## Installation

```bash
pip install -e .
```

Or install dependencies directly:

```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MIGRATORXPRESS_PATH` | `./MigratorXpress` | Path to MigratorXpress binary |
| `MIGRATORXPRESS_TIMEOUT` | `3600` | Command execution timeout in seconds |
| `MIGRATORXPRESS_LOG_DIR` | `./logs` | Directory for execution logs |
| `LOG_LEVEL` | `INFO` | Server logging level |

Copy `.env.example` to `.env` and adjust values:

```bash
cp .env.example .env
```

### Claude Code Configuration

Add to your Claude Code MCP settings:

```json
{
  "mcpServers": {
    "migratorxpress": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/migratorxpress-mcp",
      "env": {
        "MIGRATORXPRESS_PATH": "/path/to/MigratorXpress"
      }
    }
  }
}
```

## Tools

### 1. `preview_command`

Build and preview a MigratorXpress CLI command without executing it. License text is automatically masked in the display output.

**Required parameters:** `auth_file`, `source_db_auth_id`, `source_db_name`, `target_db_auth_id`, `target_db_name`, `migration_db_auth_id`

### 2. `execute_command`

Execute a previously previewed command. Requires `confirmation: true` as a safety mechanism.

### 3. `validate_auth_file`

Validate that an authentication file exists, is valid JSON, and optionally check for specific `auth_id` entries.

### 4. `list_capabilities`

List supported source/target databases, tasks, migration DB modes, load modes, and FK modes.

### 5. `suggest_workflow`

Given a source database type, target database type, and optional constraint flag, suggest the full sequence of migration tasks with example commands.

### 6. `get_version`

Report MigratorXpress version and capabilities.

## Workflow Example

A typical migration from Oracle to PostgreSQL:

```
Step 1: translate  — Translate Oracle DDL to PostgreSQL-compatible DDL
Step 2: create     — Create target tables from translated DDL
Step 3: transfer   — Transfer data from source to target
Step 4: diff       — Verify row counts match between source and target
Step 5: copy_pk    — Copy primary key constraints
        copy_ak    — Copy alternate key (unique) constraints
        copy_fk    — Copy foreign key constraints
```

Or run all steps in a single invocation with `--task_list all`.

## Development

### Running Tests

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

## License

MIT
