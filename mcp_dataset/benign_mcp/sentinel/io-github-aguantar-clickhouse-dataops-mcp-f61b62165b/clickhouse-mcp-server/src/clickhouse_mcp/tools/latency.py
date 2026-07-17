"""Tool: pipeline_latency — CDC pipeline per-segment latency analysis."""

import json

from ..client import execute_query

VALID_PERIODS = {"10m": 10, "1h": 60, "6h": 360, "24h": 1440}


def run(market: str = "", period: str = "1h") -> str:
    """Analyze CDC pipeline latency by segment (source→cdc→flink→insert)."""
    if period not in VALID_PERIODS:
        return json.dumps({"error": f"Invalid period. Allowed: {list(VALID_PERIODS.keys())}"})

    minutes = VALID_PERIODS[period]
    market_filter = f"AND market = '{market}'" if market else ""

    # Per-segment latency
    try:
        cols, rows = execute_query(
            f"""
            SELECT
                count() as total_trades,
                min(source_ts) as time_from,
                max(source_ts) as time_to,

                round(quantile(0.5)(dateDiff('millisecond', source_ts, cdc_ts)), 2) as source_to_cdc_p50,
                round(quantile(0.95)(dateDiff('millisecond', source_ts, cdc_ts)), 2) as source_to_cdc_p95,
                round(quantile(0.99)(dateDiff('millisecond', source_ts, cdc_ts)), 2) as source_to_cdc_p99,
                max(dateDiff('millisecond', source_ts, cdc_ts)) as source_to_cdc_max,

                round(quantile(0.5)(dateDiff('millisecond', cdc_ts, flink_ts)), 2) as cdc_to_flink_p50,
                round(quantile(0.95)(dateDiff('millisecond', cdc_ts, flink_ts)), 2) as cdc_to_flink_p95,
                round(quantile(0.99)(dateDiff('millisecond', cdc_ts, flink_ts)), 2) as cdc_to_flink_p99,
                max(dateDiff('millisecond', cdc_ts, flink_ts)) as cdc_to_flink_max,

                round(quantile(0.5)(dateDiff('millisecond', flink_ts, inserted_at)), 2) as flink_to_insert_p50,
                round(quantile(0.95)(dateDiff('millisecond', flink_ts, inserted_at)), 2) as flink_to_insert_p95,
                round(quantile(0.99)(dateDiff('millisecond', flink_ts, inserted_at)), 2) as flink_to_insert_p99,
                max(dateDiff('millisecond', flink_ts, inserted_at)) as flink_to_insert_max,

                round(quantile(0.5)(dateDiff('millisecond', source_ts, inserted_at)), 2) as e2e_p50,
                round(quantile(0.95)(dateDiff('millisecond', source_ts, inserted_at)), 2) as e2e_p95,
                round(quantile(0.99)(dateDiff('millisecond', source_ts, inserted_at)), 2) as e2e_p99,
                max(dateDiff('millisecond', source_ts, inserted_at)) as e2e_max
            FROM cdc_pipeline.crypto_trades
            WHERE source_ts >= now() - INTERVAL {minutes} MINUTE
            {market_filter}
            """,
            "cdc_pipeline",
        )
    except Exception as e:
        return json.dumps({"error": f"Latency query failed: {e}"})

    if not rows or rows[0][0] == 0:
        return json.dumps({"error": "No data in the specified period"})

    r = rows[0]
    result = {
        "overall": {
            "total_trades": r[0],
            "time_range": {"from": str(r[1]), "to": str(r[2])},
        },
        "latency_ms": {
            "source_to_cdc": {"p50": r[3], "p95": r[4], "p99": r[5], "max": r[6]},
            "cdc_to_flink": {"p50": r[7], "p95": r[8], "p99": r[9], "max": r[10]},
            "flink_to_insert": {"p50": r[11], "p95": r[12], "p99": r[13], "max": r[14]},
            "end_to_end": {"p50": r[15], "p95": r[16], "p99": r[17], "max": r[18]},
        },
    }

    # Freshness
    try:
        _, fresh_rows = execute_query(
            "SELECT max(source_ts), dateDiff('second', max(source_ts), now64(3)) FROM cdc_pipeline.crypto_trades"
        )
        if fresh_rows:
            result["freshness"] = {
                "last_trade_at": str(fresh_rows[0][0]),
                "seconds_behind": fresh_rows[0][1],
            }
    except Exception:
        pass

    # Per-market breakdown
    try:
        _, market_rows = execute_query(
            f"""
            SELECT
                market,
                count() as trades,
                round(quantile(0.5)(dateDiff('millisecond', source_ts, inserted_at)), 2) as e2e_p50,
                round(quantile(0.99)(dateDiff('millisecond', source_ts, inserted_at)), 2) as e2e_p99
            FROM cdc_pipeline.crypto_trades
            WHERE source_ts >= now() - INTERVAL {minutes} MINUTE
            GROUP BY market ORDER BY trades DESC
            """,
            "cdc_pipeline",
        )
        result["by_market"] = [
            {"market": row[0], "trades": row[1], "e2e_p50": row[2], "e2e_p99": row[3]}
            for row in market_rows
        ]
    except Exception:
        pass

    return json.dumps(result, default=str)
