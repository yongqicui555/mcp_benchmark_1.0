"""Tool: slow_queries — Detect slow queries with root cause diagnosis."""

import json

from ..client import execute_query


def _diagnose(row: dict) -> str:
    """Generate diagnosis for a slow query."""
    reasons = []

    if row["read_rows"] > 10_000_000:
        reasons.append(
            f"Full scan: read {row['read_rows']:,} rows. "
            "Add time-based WHERE clause to leverage partition pruning."
        )

    mem = row.get("raw_memory", 0)
    if mem > 1_000_000_000:
        readable = f"{mem / 1_000_000_000:.1f}GB"
        reasons.append(
            f"High memory usage ({readable}). Consider adding LIMIT or using sampling."
        )

    if row["duration_ms"] > 10_000:
        query_upper = row["query"].upper()
        if "GROUP BY" in query_upper:
            reasons.append(
                "Slow aggregation. Consider using pre-aggregated tables "
                "(int_ohlcv_1h, mart_daily_summary) instead of raw crypto_trades."
            )

    if row.get("exception"):
        reasons.append(f"Error occurred: {row['exception'][:200]}")

    if not reasons:
        reasons.append("No obvious issue detected. Check concurrent load or complex JOINs.")

    return " | ".join(reasons)


def run(hours: int = 24, min_duration_ms: int = 1000, limit: int = 20) -> str:
    """Find slow queries in system.query_log with root cause diagnosis."""
    try:
        cols, rows = execute_query(
            f"""
            SELECT
                event_time,
                query_duration_ms,
                query,
                read_rows,
                read_bytes,
                memory_usage,
                tables,
                exception
            FROM system.query_log
            WHERE type = 'QueryFinish'
              AND event_time >= now() - INTERVAL {hours} HOUR
              AND query_duration_ms >= {min_duration_ms}
              AND query NOT LIKE '%system.query_log%'
            ORDER BY query_duration_ms DESC
            LIMIT {limit}
            """
        )
    except Exception as e:
        return json.dumps({"error": f"Failed to query system.query_log: {e}"})

    queries = []
    for row in rows:
        entry = {
            "event_time": str(row[0]),
            "duration_ms": row[1],
            "query": str(row[2])[:200],
            "read_rows": row[3],
            "read_bytes_readable": _readable_bytes(row[4]),
            "raw_memory": row[5],
            "memory_usage_readable": _readable_bytes(row[5]),
            "tables": row[6],
            "exception": str(row[7]) if row[7] else "",
        }
        entry["diagnosis"] = _diagnose(entry)
        queries.append(entry)

    # Summary
    table_counts: dict[str, int] = {}
    for q in queries:
        for t in (q["tables"] or []):
            table_counts[t] = table_counts.get(t, 0) + 1

    result = {
        "queries": queries,
        "summary": {
            "total_slow": len(queries),
            "avg_duration_ms": (
                round(sum(q["duration_ms"] for q in queries) / len(queries), 1)
                if queries
                else 0
            ),
            "top_tables": sorted(table_counts.items(), key=lambda x: x[1], reverse=True)[:5],
        },
    }

    return json.dumps(result, default=str)


def _readable_bytes(b: int) -> str:
    for unit in ["B", "KiB", "MiB", "GiB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TiB"
