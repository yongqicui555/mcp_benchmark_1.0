import os


CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")
CLICKHOUSE_DATABASE = os.getenv("CLICKHOUSE_DATABASE", "cdc_pipeline")

QUERY_TIMEOUT = int(os.getenv("CLICKHOUSE_QUERY_TIMEOUT", "30"))
MAX_ROWS_DEFAULT = 1000
MAX_ROWS_LIMIT = 10000

TABLE_DESCRIPTIONS = {
    "cdc_pipeline.crypto_trades": "CDC real-time trade data (Upbit: BTC/ETH/SOL/XRP/DOGE)",
    "cdc_pipeline.stg_trades": "dbt staging view — cleaned crypto_trades",
    "cdc_pipeline.int_ohlcv_1h": "dbt intermediate — hourly OHLCV candles",
    "cdc_pipeline.int_ohlcv_daily": "dbt intermediate — daily OHLCV candles",
    "cdc_pipeline.mart_daily_summary": "dbt mart — daily summary report",
    "cdc_pipeline.mart_volume_spike": "dbt mart — volume spike detection",
    "cdc_pipeline.mart_alert_rate": "dbt mart — anomaly alert rate",
    "cdc_pipeline.anomaly_alerts": "Flink anomaly detection alerts",
    "cdc_pipeline.trade_aggregations": "Flink real-time aggregation (1-min window)",
    "cdc_pipeline.mv_latency_stats": "Materialized View — CDC latency stats",
    "cdc_pipeline.coin_metadata": "Coin metadata (dbt seed)",
    "circuit_connect.fact_sessions": "Circuit Connect game sessions",
    "circuit_connect.game_events": "Circuit Connect raw events",
    "circuit_connect.game_alerts": "Circuit Connect anomaly alerts",
    "circuit_connect.dim_users": "Circuit Connect user profiles",
    "circuit_connect.dim_leaderboard": "Circuit Connect leaderboard",
}
