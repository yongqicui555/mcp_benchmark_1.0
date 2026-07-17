# clickhouse-dataops-mcp

mcp-name: io.github.Aguantar/clickhouse-dataops-mcp

A DataOps-focused MCP server for ClickHouse with query optimization, pipeline latency analysis, and data quality monitoring.

## Features

Unlike generic ClickHouse MCP servers that only run queries, this server acts as a **query optimization advisor**:

- **`ch_query`** — Execute SELECT with automatic partition pruning warnings
- **`ch_explain_query`** — EXPLAIN-based analysis with optimization suggestions
- **`ch_table_schema`** — Comprehensive table metadata (columns, keys, partitions, samples)
- **`ch_pipeline_latency`** — CDC pipeline per-segment latency (p50/p95/p99)
- **`ch_data_quality`** — Null/duplicate/gap detection with market coverage checks
- **`ch_slow_queries`** — Slow query detection with root cause diagnosis
- **`ch_disk_usage`** — Disk analysis with TTL and optimization recommendations
- **`ch_list_tables`** — Table catalog with built-in descriptions

## Safety

All queries are read-only. DDL/DML operations are blocked at the SQL validation layer:

- Blocked: `DROP`, `TRUNCATE`, `DELETE`, `ALTER`, `INSERT`, `UPDATE`, `CREATE`, etc.
- Multi-statement queries blocked (`;` separator)
- Comment-based bypass prevented (comments stripped before validation)
- System tables restricted to allowlist
- Query timeout: 30 seconds
- Row limit enforcement

## Installation

```bash
pip install clickhouse-dataops-mcp
```

## Usage with Claude Code

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "clickhouse": {
      "command": "clickhouse-mcp-server",
      "env": {
        "CLICKHOUSE_HOST": "localhost",
        "CLICKHOUSE_PORT": "8123",
        "CLICKHOUSE_DATABASE": "cdc_pipeline"
      }
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CLICKHOUSE_HOST` | `localhost` | ClickHouse HTTP host |
| `CLICKHOUSE_PORT` | `8123` | ClickHouse HTTP port |
| `CLICKHOUSE_USER` | `default` | ClickHouse username |
| `CLICKHOUSE_PASSWORD` | (empty) | ClickHouse password |
| `CLICKHOUSE_DATABASE` | `cdc_pipeline` | Default database |
| `CLICKHOUSE_QUERY_TIMEOUT` | `30` | Query timeout in seconds |

## License

MIT
