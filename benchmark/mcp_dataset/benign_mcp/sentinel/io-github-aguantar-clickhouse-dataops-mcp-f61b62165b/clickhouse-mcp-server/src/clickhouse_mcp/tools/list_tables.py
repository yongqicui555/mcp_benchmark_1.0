"""Tool: list_tables — List tables with metadata and built-in descriptions."""

import json

from ..client import execute_query
from ..config import CLICKHOUSE_DATABASE, TABLE_DESCRIPTIONS


def run(database: str = "") -> str:
    """List all tables in a database with engine, keys, row counts, and descriptions."""
    if not database:
        database = CLICKHOUSE_DATABASE

    try:
        _, table_rows = execute_query(
            f"""
            SELECT name, engine, partition_key, sorting_key
            FROM system.tables
            WHERE database = '{database}'
              AND name NOT LIKE '.inner%'
            ORDER BY name
            """
        )
    except Exception as e:
        return json.dumps({"error": f"Failed to list tables: {e}"})

    # Get row counts and disk sizes
    size_map: dict[str, dict] = {}
    try:
        _, size_rows = execute_query(
            f"""
            SELECT table, sum(rows) as rows, formatReadableSize(sum(bytes_on_disk)) as disk_size
            FROM system.parts
            WHERE active AND database = '{database}' AND table NOT LIKE '.inner%'
            GROUP BY table
            """
        )
        for row in size_rows:
            size_map[row[0]] = {"row_count": row[1], "disk_size": row[2]}
    except Exception:
        pass

    tables = []
    for row in table_rows:
        name = row[0]
        fqn = f"{database}.{name}"
        info = {
            "name": name,
            "engine": row[1],
            "partition_key": row[2] or "none",
            "sorting_key": row[3] or "none",
            "row_count": size_map.get(name, {}).get("row_count", 0),
            "disk_size": size_map.get(name, {}).get("disk_size", "0 B"),
            "description": TABLE_DESCRIPTIONS.get(fqn, ""),
        }
        tables.append(info)

    return json.dumps({"database": database, "tables": tables}, default=str)
