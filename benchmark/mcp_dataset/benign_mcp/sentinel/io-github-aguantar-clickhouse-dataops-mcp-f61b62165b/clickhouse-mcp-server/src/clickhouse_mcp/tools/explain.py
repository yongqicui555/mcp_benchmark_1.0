"""Tool: explain_query — EXPLAIN-based query analysis with optimization suggestions."""

import json
import re

from ..client import execute_query
from ..safety import UnsafeQueryError, validate_query


def _parse_plan(plan_lines: list[str]) -> dict:
    """Extract structured info from EXPLAIN PLAN output."""
    info = {
        "reads_from": [],
        "partition_pruning": False,
        "sorting_key_used": False,
    }
    for line in plan_lines:
        # Detect table reads
        match = re.search(r"ReadFromMergeTree\s*\((\S+)\)", line)
        if match:
            info["reads_from"].append(match.group(1))
        if "Partition" in line and "pruning" in line.lower():
            info["partition_pruning"] = True
        if "PrimaryKey" in line or "Key Condition" in line:
            info["sorting_key_used"] = True
    return info


def _generate_suggestions(sql: str, plan_info: dict) -> list[str]:
    """Generate optimization suggestions based on query and plan analysis."""
    suggestions = []
    upper = sql.upper()

    # 1. Partition key not in WHERE
    partition_keys = ["SOURCE_TS", "DETECTED_AT", "SESSION_START", "EVENT_DATE", "WINDOW_START"]
    has_where = "WHERE" in upper
    has_partition_filter = any(k in upper for k in partition_keys)

    if has_where and not has_partition_filter and plan_info["reads_from"]:
        suggestions.append(
            "Partition pruning may not be active. Add a time-based condition "
            "(e.g., WHERE source_ts >= '...') to reduce scanned partitions."
        )
    if not has_where and plan_info["reads_from"]:
        suggestions.append(
            "No WHERE clause — full table scan. Add filters to leverage partitioning."
        )

    # 2. Sorting key not used
    sorting_first_cols = ["MARKET", "ALERT_TYPE", "USER_KEY", "EVENT_TYPE", "TRADE_DATE", "HOUR"]
    has_sorting_filter = any(k in upper for k in sorting_first_cols)
    if has_where and not has_sorting_filter:
        suggestions.append(
            "Consider filtering on the first column of the sorting key (e.g., market) "
            "to improve index utilization."
        )

    # 3. SELECT *
    if re.search(r"SELECT\s+\*", upper):
        suggestions.append(
            "SELECT * reads all columns. Specify only needed columns to reduce I/O."
        )

    # 4. GROUP BY + ORDER BY mismatch
    group_match = re.search(r"GROUP\s+BY\s+(.+?)(?:ORDER|LIMIT|HAVING|$)", upper)
    order_match = re.search(r"ORDER\s+BY\s+(.+?)(?:LIMIT|$)", upper)
    if group_match and order_match:
        group_cols = group_match.group(1).strip()
        order_cols = order_match.group(1).strip()
        if group_cols != order_cols:
            suggestions.append(
                "ORDER BY columns differ from GROUP BY — this requires an extra sort step. "
                "Aligning them can eliminate the additional sort."
            )

    # 5. Suggest pre-aggregated tables
    if "CRYPTO_TRADES" in upper and any(
        k in upper for k in ["GROUP BY", "SUM(", "AVG(", "COUNT("]
    ):
        suggestions.append(
            "For aggregations on crypto_trades, consider using pre-aggregated tables: "
            "int_ohlcv_1h (hourly), int_ohlcv_daily (daily), or mart_daily_summary."
        )

    return suggestions


def run(sql: str, database: str = "cdc_pipeline") -> str:
    """Analyze a query's execution plan and provide optimization suggestions."""
    try:
        cleaned = validate_query(sql)
    except UnsafeQueryError as e:
        return json.dumps({"error": str(e)})

    result = {}

    # EXPLAIN PLAN
    try:
        _, plan_rows = execute_query(f"EXPLAIN PLAN {cleaned}", database)
        plan_lines = [str(row[0]) for row in plan_rows]
        result["plan"] = "\n".join(plan_lines)
    except Exception as e:
        return json.dumps({"error": f"EXPLAIN PLAN failed: {str(e)}"})

    # EXPLAIN PIPELINE
    try:
        _, pipeline_rows = execute_query(f"EXPLAIN PIPELINE {cleaned}", database)
        result["pipeline"] = "\n".join(str(row[0]) for row in pipeline_rows)
    except Exception as e:
        result["pipeline"] = f"EXPLAIN PIPELINE not available: {str(e)}"

    # Analysis
    plan_info = _parse_plan(plan_lines)
    result["analysis"] = plan_info
    result["suggestions"] = _generate_suggestions(cleaned, plan_info)

    return json.dumps(result, default=str)
