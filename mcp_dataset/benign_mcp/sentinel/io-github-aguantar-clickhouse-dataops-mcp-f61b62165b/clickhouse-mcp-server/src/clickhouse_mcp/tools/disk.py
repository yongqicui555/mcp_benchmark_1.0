"""Tool: disk_usage — Table and partition disk usage with recommendations."""

import json

from ..client import execute_query
from ..config import CLICKHOUSE_DATABASE


def run(database: str = "") -> str:
    """Analyze disk usage by table and partition with recommendations."""
    if not database:
        database = CLICKHOUSE_DATABASE

    result = {"database": database}

    # Total disk
    try:
        _, rows = execute_query(
            f"""
            SELECT
                formatReadableSize(sum(bytes_on_disk)) as total_disk,
                sum(bytes_on_disk) as total_bytes
            FROM system.parts
            WHERE active AND database = '{database}'
            """
        )
        result["total_disk"] = rows[0][0] if rows else "0 B"
        total_bytes = rows[0][1] if rows else 0
    except Exception as e:
        return json.dumps({"error": f"Failed to query disk usage: {e}"})

    # By table
    try:
        _, rows = execute_query(
            f"""
            SELECT
                table,
                engine,
                sum(rows) as rows,
                formatReadableSize(sum(bytes_on_disk)) as disk_size,
                sum(bytes_on_disk) as raw_bytes,
                count() as parts
            FROM system.parts
            WHERE active AND database = '{database}'
            GROUP BY table, engine
            ORDER BY sum(bytes_on_disk) DESC
            """
        )
        result["by_table"] = [
            {
                "table": row[0],
                "engine": row[1],
                "rows": row[2],
                "disk_size": row[3],
                "parts": row[5],
                "pct_of_total": round(row[4] * 100.0 / total_bytes, 1) if total_bytes else 0,
            }
            for row in rows
            if not row[0].startswith(".inner")
        ]
    except Exception:
        pass

    # By partition (top 20)
    try:
        _, rows = execute_query(
            f"""
            SELECT table, partition, sum(rows) as rows,
                   formatReadableSize(sum(bytes_on_disk)) as disk_size
            FROM system.parts
            WHERE active AND database = '{database}' AND table NOT LIKE '.inner%'
            GROUP BY table, partition
            ORDER BY sum(bytes_on_disk) DESC
            LIMIT 20
            """
        )
        result["by_partition"] = [
            {"table": row[0], "partition": row[1], "rows": row[2], "size": row[3]}
            for row in rows
        ]
    except Exception:
        pass

    # TTL info
    try:
        _, rows = execute_query(
            f"""
            SELECT name, engine_full
            FROM system.tables
            WHERE database = '{database}' AND engine_full LIKE '%TTL%'
            """
        )
        result["ttl_info"] = []
        for row in rows:
            engine_full = str(row[1])
            if "TTL" in engine_full:
                ttl_start = engine_full.index("TTL")
                ttl_expr = engine_full[ttl_start:].split("\n")[0].strip()
                result["ttl_info"].append({"table": row[0], "ttl": ttl_expr})
    except Exception:
        pass

    # Recommendations
    recommendations = []
    for t in result.get("by_table", []):
        if t["parts"] > 50:
            recommendations.append(
                f"{t['table']}: {t['parts']} parts — consider OPTIMIZE TABLE to merge."
            )
    # Check for large tables without TTL
    ttl_tables = {t["table"] for t in result.get("ttl_info", [])}
    for t in result.get("by_table", []):
        if t["rows"] > 1_000_000 and t["table"] not in ttl_tables:
            recommendations.append(
                f"{t['table']}: {t['rows']:,} rows with no TTL — consider adding TTL for storage management."
            )

    result["recommendations"] = recommendations

    return json.dumps(result, default=str)
