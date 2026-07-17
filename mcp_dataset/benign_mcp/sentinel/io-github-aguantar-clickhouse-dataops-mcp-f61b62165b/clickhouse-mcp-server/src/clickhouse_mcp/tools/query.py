"""Tool: query — Execute SELECT queries with automatic partition pruning analysis."""

import json
import re

from ..client import execute_query, execute_query_with_stats
from ..config import MAX_ROWS_DEFAULT, MAX_ROWS_LIMIT
from ..safety import UnsafeQueryError, ensure_limit, validate_query


def _check_partition_pruning(sql: str, database: str) -> str | None:
    """Run EXPLAIN and check if partition pruning is happening."""
    try:
        cols, rows = execute_query(f"EXPLAIN PLAN {sql}", database)
        plan_text = "\n".join(str(row[0]) for row in rows)

        # Heuristic: if ReadFromMergeTree is present but no partition filter mentioned
        if "ReadFromMergeTree" in plan_text:
            # Check if the query references a partitioned table without partition key in WHERE
            upper_sql = sql.upper()
            # Common partition keys in our schema
            partition_keys = ["SOURCE_TS", "DETECTED_AT", "SESSION_START", "EVENT_DATE", "WINDOW_START"]
            has_partition_filter = any(k in upper_sql for k in partition_keys)
            if not has_partition_filter and "WHERE" in upper_sql:
                return (
                    "Warning: Query may not leverage partition pruning. "
                    "Consider adding a time-based condition (e.g., WHERE source_ts >= ...) "
                    "to reduce scanned data."
                )
            if "WHERE" not in upper_sql:
                return (
                    "Warning: No WHERE clause detected. Full table scan will occur. "
                    "Add time-based filters to leverage partitioning."
                )
    except Exception:
        pass
    return None


def run(sql: str, database: str = "cdc_pipeline", max_rows: int = MAX_ROWS_DEFAULT) -> str:
    """Execute a SELECT query against ClickHouse with safety checks."""
    try:
        cleaned = validate_query(sql)
    except UnsafeQueryError as e:
        return json.dumps({"error": str(e)})

    max_rows = min(max_rows, MAX_ROWS_LIMIT)
    safe_sql = ensure_limit(cleaned, max_rows)

    # Check partition pruning before execution
    warning = _check_partition_pruning(cleaned, database)

    try:
        columns, rows, stats = execute_query_with_stats(safe_sql, database)
    except Exception as e:
        return json.dumps({"error": f"Query execution failed: {str(e)}"})

    result = {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "statistics": stats,
    }
    if warning:
        result["warning"] = warning

    return json.dumps(result, default=str)
