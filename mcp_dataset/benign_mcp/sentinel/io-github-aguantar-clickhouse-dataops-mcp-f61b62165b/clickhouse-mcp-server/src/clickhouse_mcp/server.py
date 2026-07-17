"""ClickHouse MCP Server — DataOps-focused query advisor."""

from mcp.server.fastmcp import FastMCP

from .config import MAX_ROWS_DEFAULT
from .tools import disk, explain, latency, list_tables, quality, query, schema, slow_queries

mcp = FastMCP(
    "clickhouse-mcp-server",
    instructions=(
        "DataOps-focused ClickHouse MCP server with query optimization, "
        "pipeline latency analysis, data quality monitoring, and slow query diagnosis. "
        "Read-only access with safety enforcement."
    ),
)


@mcp.tool()
def ch_query(sql: str, database: str = "cdc_pipeline", max_rows: int = MAX_ROWS_DEFAULT) -> str:
    """Execute a read-only SQL query against ClickHouse.

    Runs SELECT queries with automatic safety validation (DDL/DML blocked),
    LIMIT enforcement, and partition pruning analysis. Returns results with
    a warning if the query doesn't leverage partitioning efficiently.

    Args:
        sql: SELECT query to execute
        database: Target database (default: cdc_pipeline)
        max_rows: Maximum rows to return (default: 1000, max: 10000)
    """
    return query.run(sql, database, max_rows)


@mcp.tool()
def ch_explain_query(sql: str, database: str = "cdc_pipeline") -> str:
    """Analyze a query's execution plan and suggest optimizations.

    Runs EXPLAIN PLAN and EXPLAIN PIPELINE, then provides structured analysis:
    - Whether partition pruning is active
    - Whether sorting keys are utilized
    - Specific optimization suggestions (add time filters, use pre-aggregated tables, etc.)

    This is the key differentiator from generic ClickHouse tools — it doesn't just
    execute queries, it advises on how to write better ones.

    Args:
        sql: The SELECT query to analyze
        database: Target database (default: cdc_pipeline)
    """
    return explain.run(sql, database)


@mcp.tool()
def ch_table_schema(table: str, database: str = "cdc_pipeline") -> str:
    """Get comprehensive table metadata: columns, engine, keys, partitions, and sample data.

    Returns column types, partition/sorting/primary keys, TTL settings,
    row counts, disk usage, partition breakdown, and 5 sample rows.
    Essential for understanding table structure before writing queries.

    Args:
        table: Table name
        database: Database name (default: cdc_pipeline)
    """
    return schema.run(table, database)


@mcp.tool()
def ch_pipeline_latency(market: str = "", period: str = "1h") -> str:
    """Analyze CDC pipeline latency by segment.

    Measures latency at each stage of the pipeline:
    - source_to_cdc: Upbit → Debezium/Kafka
    - cdc_to_flink: Kafka → Flink processing
    - flink_to_insert: Flink → ClickHouse write
    - end_to_end: total source_ts → inserted_at

    Each segment reports p50, p95, p99, and max latency in milliseconds.
    Also includes data freshness (seconds behind real-time) and per-market breakdown.

    Args:
        market: Filter by market (e.g., "KRW-BTC"). Empty = all markets
        period: Time window — "10m", "1h", "6h", or "24h" (default: "1h")
    """
    return latency.run(market, period)


@mcp.tool()
def ch_data_quality(
    table: str = "crypto_trades", database: str = "cdc_pipeline", check_date: str = ""
) -> str:
    """Run data quality checks: nulls, duplicates, gaps, and market coverage.

    Checks for a specific date:
    - Null/empty values per column
    - Duplicate rows by primary key
    - Hourly data gaps (missing time windows)
    - Market coverage (are all 5 coins present?)
    - Data freshness

    Args:
        table: Table to check (default: crypto_trades)
        database: Database name (default: cdc_pipeline)
        check_date: Date to check in YYYY-MM-DD format (default: today)
    """
    return quality.run(table, database, check_date)


@mcp.tool()
def ch_slow_queries(hours: int = 24, min_duration_ms: int = 1000, limit: int = 20) -> str:
    """Find slow queries with root cause diagnosis.

    Scans system.query_log for queries exceeding the duration threshold,
    then generates a diagnosis for each:
    - Full scan detection (high read_rows without partition pruning)
    - Memory-intensive query detection
    - Aggregation optimization suggestions (use pre-aggregated tables)
    - Error detection

    Args:
        hours: Look back period in hours (default: 24)
        min_duration_ms: Minimum query duration to report (default: 1000ms)
        limit: Maximum number of slow queries to return (default: 20)
    """
    return slow_queries.run(hours, min_duration_ms, limit)


@mcp.tool()
def ch_disk_usage(database: str = "cdc_pipeline") -> str:
    """Analyze disk usage by table and partition with recommendations.

    Returns:
    - Total disk usage for the database
    - Per-table breakdown (rows, size, parts, percentage)
    - Per-partition breakdown (top 20 by size)
    - TTL information
    - Recommendations (excessive parts, missing TTL on large tables)

    Args:
        database: Database to analyze (default: cdc_pipeline)
    """
    return disk.run(database)


@mcp.tool()
def ch_list_tables(database: str = "cdc_pipeline") -> str:
    """List all tables with metadata and built-in descriptions.

    Returns table name, engine type, partition/sorting keys, row count,
    disk size, and a human-readable description of each table's purpose.
    Use this as the starting point to understand what data is available.

    Args:
        database: Database to list (default: cdc_pipeline)
    """
    return list_tables.run(database)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
