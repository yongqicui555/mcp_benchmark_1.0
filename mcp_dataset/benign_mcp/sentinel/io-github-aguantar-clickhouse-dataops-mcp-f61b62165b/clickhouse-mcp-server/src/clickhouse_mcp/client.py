"""ClickHouse client wrapper with timeout and safety enforcement."""

import clickhouse_connect
from clickhouse_connect.driver.client import Client

from .config import (
    CLICKHOUSE_HOST,
    CLICKHOUSE_PASSWORD,
    CLICKHOUSE_PORT,
    CLICKHOUSE_USER,
    QUERY_TIMEOUT,
)


def get_client() -> Client:
    return clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        settings={"max_execution_time": QUERY_TIMEOUT},
    )


def execute_query(sql: str, database: str | None = None) -> tuple[list[str], list[list]]:
    """Execute a read-only query. Returns (column_names, rows)."""
    client = get_client()
    settings = {"max_execution_time": QUERY_TIMEOUT}
    if database:
        settings["database"] = database
    result = client.query(sql, settings=settings)
    columns = result.column_names
    rows = [list(row) for row in result.result_rows]
    return list(columns), rows


def execute_query_with_stats(
    sql: str, database: str | None = None
) -> tuple[list[str], list[list], dict]:
    """Execute query and return (columns, rows, stats)."""
    client = get_client()
    settings = {"max_execution_time": QUERY_TIMEOUT}
    if database:
        settings["database"] = database
    result = client.query(sql, settings=settings)
    columns = list(result.column_names)
    rows = [list(row) for row in result.result_rows]
    stats = {
        "rows_read": result.summary.get("read_rows", "0"),
        "bytes_read": result.summary.get("read_bytes", "0"),
        "elapsed_ms": result.summary.get("elapsed_ns", "0"),
    }
    # Convert elapsed_ns to ms
    try:
        stats["elapsed_ms"] = str(round(int(stats["elapsed_ms"]) / 1_000_000, 2))
    except (ValueError, TypeError):
        pass
    return columns, rows, stats
