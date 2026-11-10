"""Tool: data_quality — Data quality checks (nulls, duplicates, gaps, market coverage)."""

import json
from datetime import date, timedelta

from ..client import execute_query
from ..config import CLICKHOUSE_DATABASE


# Known markets for completeness check
EXPECTED_MARKETS = {"KRW-BTC", "KRW-ETH", "KRW-SOL", "KRW-XRP", "KRW-DOGE"}


def run(
    table: str = "crypto_trades",
    database: str = "",
    check_date: str = "",
) -> str:
    """Run data quality checks: nulls, duplicates, gaps, and market coverage."""
    if not database:
        database = CLICKHOUSE_DATABASE
    if not check_date:
        check_date = str(date.today())

    fqn = f"{database}.{table}"
    result = {"table": fqn, "date": check_date}

    # Row count for the date
    try:
        time_col = _guess_time_column(table)
        _, rows = execute_query(
            f"""
            SELECT count() FROM {fqn}
            WHERE toDate({time_col}) = '{check_date}'
            """
        )
        result["row_count"] = rows[0][0] if rows else 0
    except Exception as e:
        return json.dumps({"error": f"Row count failed: {e}"})

    # Null check
    try:
        _, col_rows = execute_query(
            f"SELECT name FROM system.columns WHERE database='{database}' AND table='{table}'"
        )
        null_results = []
        for col_row in col_rows:
            col_name = col_row[0]
            _, nr = execute_query(
                f"""
                SELECT
                    countIf(isNull({col_name}) OR toString({col_name}) = '') as null_count,
                    round(countIf(isNull({col_name}) OR toString({col_name}) = '') * 100.0 / count(), 4) as null_pct
                FROM {fqn}
                WHERE toDate({time_col}) = '{check_date}'
                """
            )
            if nr and nr[0][0] > 0:
                null_results.append({"column": col_name, "null_count": nr[0][0], "null_pct": nr[0][1]})
        result["null_check"] = null_results
    except Exception:
        result["null_check"] = "check failed"

    # Duplicate check (by primary key heuristic)
    try:
        pk_col = _guess_pk_column(table)
        _, dup_rows = execute_query(
            f"""
            SELECT count() as total, uniqExact({pk_col}) as distinct_count
            FROM {fqn}
            WHERE toDate({time_col}) = '{check_date}'
            """
        )
        if dup_rows:
            total, distinct = dup_rows[0]
            dup_pct = round((total - distinct) * 100.0 / total, 4) if total > 0 else 0
            result["duplicate_check"] = {
                "total": total,
                "distinct": distinct,
                "duplicate_pct": dup_pct,
            }
    except Exception:
        result["duplicate_check"] = "check failed"

    # Gap detection (hourly)
    try:
        _, gap_rows = execute_query(
            f"""
            SELECT toStartOfHour({time_col}) as hour, count() as cnt
            FROM {fqn}
            WHERE toDate({time_col}) = '{check_date}'
            GROUP BY hour ORDER BY hour
            """
        )
        hourly = {str(row[0]): row[1] for row in gap_rows}
        gaps = []
        for h in range(24):
            hour_str = f"{check_date} {h:02d}:00:00"
            if hour_str not in hourly and any(hour_str[:10] in k for k in hourly):
                gaps.append(f"{hour_str} — no data")
        result["gap_detection"] = {
            "hourly_counts": [{"hour": str(r[0]), "count": r[1]} for r in gap_rows],
            "gaps": gaps,
        }
    except Exception:
        result["gap_detection"] = "check failed"

    # Market coverage (crypto_trades specific)
    if table == "crypto_trades":
        try:
            _, market_rows = execute_query(
                f"""
                SELECT groupArray(DISTINCT market)
                FROM {fqn}
                WHERE toDate({time_col}) = '{check_date}'
                """
            )
            if market_rows:
                present = set(market_rows[0][0])
                missing = EXPECTED_MARKETS - present
                result["market_coverage"] = {
                    "expected": sorted(EXPECTED_MARKETS),
                    "present": sorted(present),
                    "missing": sorted(missing),
                }
        except Exception:
            pass

    # Freshness
    try:
        _, fresh_rows = execute_query(
            f"SELECT max({time_col}), dateDiff('minute', max({time_col}), now()) FROM {fqn}"
        )
        if fresh_rows:
            result["freshness"] = {
                "last_record": str(fresh_rows[0][0]),
                "minutes_behind": fresh_rows[0][1],
            }
    except Exception:
        pass

    return json.dumps(result, default=str)


def _guess_time_column(table: str) -> str:
    mapping = {
        "crypto_trades": "source_ts",
        "anomaly_alerts": "detected_at",
        "trade_aggregations": "window_start",
        "fact_sessions": "toDateTime(session_start / 1000)",
        "game_events": "event_date",
        "game_alerts": "toDateTime(detected_at / 1000)",
    }
    return mapping.get(table, "inserted_at")


def _guess_pk_column(table: str) -> str:
    mapping = {
        "crypto_trades": "trade_id",
        "fact_sessions": "session_id",
        "game_events": "event_id",
    }
    return mapping.get(table, "tuple(*)")
