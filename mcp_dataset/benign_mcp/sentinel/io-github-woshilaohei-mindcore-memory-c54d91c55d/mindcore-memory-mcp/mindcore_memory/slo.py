"""
SLO (Service Level Objectives) for mindcore-memory-mcp v0.1.9.

Each operation has P95/P99 latency targets. The @track_latency decorator
records actual latencies and emits structured log warnings on SLO violations.
"""

from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable

SLO_TARGETS: dict[str, dict[str, float]] = {
    "memory_store":             {"p95": 0.050, "p99": 0.200},
    "memory_recall":            {"p95": 0.100, "p99": 0.500},
    "memory_context":           {"p95": 0.200, "p99": 1.000},
    "memory_update_confidence": {"p95": 0.030, "p99": 0.100},
    "memory_delete":            {"p95": 0.030, "p99": 0.100},
    "memory_stats":             {"p95": 0.010, "p99": 0.050},
    "health":                   {"p95": 0.005, "p99": 0.020},
}


def get_slo_target(operation: str, percentile: str = "p95") -> float:
    """Get SLO target in seconds for a given operation."""
    return SLO_TARGETS.get(operation, {}).get(percentile, 0.0)


def track_latency(operation: str):
    """Decorator: track operation latency and log SLO violations.

    Usage:
        @track_latency("memory_recall")
        def recall(self, query, ...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            import structlog
            logger = structlog.get_logger()

            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start
                p95 = get_slo_target(operation, "p95")
                p99 = get_slo_target(operation, "p99")

                # Log latency for observability (skip if no SLO defined)
                if p95 > 0:
                    log_kwargs = {
                        "operation": operation,
                        "latency_ms": round(elapsed * 1000, 2),
                        "slo_p95_ms": round(p95 * 1000, 1),
                    }
                    if elapsed > p99:
                        logger.warning("slo_violation_p99", **log_kwargs, severity="critical")
                    elif elapsed > p95:
                        logger.warning("slo_violation_p95", **log_kwargs, severity="warning")
                    else:
                        logger.debug("slo_ok", **log_kwargs)

                # Feed metrics collector if available
                try:
                    from .metrics import get_collector
                    collector = get_collector()
                    if collector:
                        collector.record_latency(operation, elapsed)
                except Exception:
                    pass
            return result
        return wrapper
    return decorator
