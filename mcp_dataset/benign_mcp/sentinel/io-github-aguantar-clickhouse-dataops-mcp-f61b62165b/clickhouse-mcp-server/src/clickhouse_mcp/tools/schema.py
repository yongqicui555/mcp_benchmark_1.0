"""Tool: table_schema — Table structure, metadata, and partition details."""

import json

from ..client import execute_query
from ..config import CLICKHOUSE_DATABASE


def run(table: str, database: str = "") -> str:
    """Get comprehensive schema info for a table."""
    if not database:
        database = CLICKHOUSE_DATABASE

    result = {"table": table, "database": database}

    # Column info
    try:
        cols, rows = execute_query(
            f"""
            SELECT name, type, is_in_partition_key, is_in_sorting_key, is_in_primary_key
            FROM system.columns
            WHERE database = '{database}' AND table = '{table}'
            ORDER BY position
            """
        )
        result["columns"] = [
            {
                "name": row[0],
                "type": row[1],
                "is_partition_key": bool(row[2]),
                "is_sorting_key": bool(row[3]),
                "is_primary_key": bool(row[4]),
            }
            for row in rows
        ]
    except Exception as e:
        return json.dumps({"error": f"Failed to get columns: {e}"})

    # Engine, keys, TTL
    try:
        _, rows = execute_query(
            f"""
            SELECT engine, partition_key, sorting_key, primary_key,
                   engine_full
            FROM system.tables
            WHERE database = '{database}' AND name = '{table}'
            """
        )
        if rows:
            row = rows[0]
            result["engine"] = row[0]
            result["partition_key"] = row[1] or "none"
            result["sorting_key"] = row[2] or "none"
            result["primary_key"] = row[3] or "none"
            # Extract TTL from engine_full
            engine_full = str(row[4])
            if "TTL" in engine_full:
                ttl_start = engine_full.index("TTL")
                result["ttl"] = engine_full[ttl_start:].split("\n")[0].strip()
    except Exception:
        pass

    # Row count, disk size, parts
    try:
        _, rows = execute_query(
            f"""
            SELECT
                sum(rows) as row_count,
                formatReadableSize(sum(bytes_on_disk)) as disk_size,
                count() as parts_count
            FROM system.parts
            WHERE active AND database = '{database}' AND table = '{table}'
            """
        )
        if rows and rows[0][0] is not None:
            result["row_count"] = rows[0][0]
            result["disk_size"] = rows[0][1]
            result["parts_count"] = rows[0][2]
    except Exception:
        pass

    # Partition details
    try:
        _, rows = execute_query(
            f"""
            SELECT partition, sum(rows) as rows, formatReadableSize(sum(bytes_on_disk)) as size
            FROM system.parts
            WHERE active AND database = '{database}' AND table = '{table}'
            GROUP BY partition
            ORDER BY partition
            """
        )
        if rows:
            result["partitions"] = [
                {"partition": row[0], "rows": row[1], "size": row[2]} for row in rows
            ]
    except Exception:
        pass

    # Sample data (5 rows)
    try:
        cols, rows = execute_query(
            f"SELECT * FROM {database}.{table} LIMIT 5"
        )
        result["sample_data"] = {"columns": cols, "rows": rows}
    except Exception:
        pass

    return json.dumps(result, default=str)
