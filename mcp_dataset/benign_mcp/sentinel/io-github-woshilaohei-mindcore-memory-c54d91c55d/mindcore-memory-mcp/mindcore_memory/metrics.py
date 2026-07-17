"""
Prometheus-compatible metrics collector — no external dependencies.

Exposes counters and histograms for all 6 memory operations.
Serves /metrics endpoint in Prometheus text format.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Optional


class MetricsCollector:
    """Thread-safe in-memory metrics collector (Prometheus text format)."""

    def __init__(self):
        self._lock = threading.Lock()
        self._counters: dict[str, int] = defaultdict(int)
        # Latency buckets: 1ms, 5ms, 10ms, 25ms, 50ms, 100ms, 250ms, 500ms, 1s, 5s, +Inf
        self._buckets = (0.001, 0.005, 0.01, 0.025, 0.05, 0.10, 0.25, 0.50, 1.0, 5.0, float("inf"))
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._start_time = time.time()
        self._uptime_seconds = 0.0

    # ------------------------------------------------------------------
    # Record
    # ------------------------------------------------------------------
    def inc_counter(self, name: str, value: int = 1):
        with self._lock:
            self._counters[name] += value

    def record_latency(self, operation: str, seconds: float):
        metric_name = f"mindcore_{operation}_latency_seconds"
        with self._lock:
            self._histograms[metric_name].append(seconds)
            # Trim to last 10000 entries to bound memory
            if len(self._histograms[metric_name]) > 10000:
                self._histograms[metric_name] = self._histograms[metric_name][-10000:]

    def record_error(self, operation: str):
        self.inc_counter(f"mindcore_{operation}_errors_total")

    def record_success(self, operation: str):
        self.inc_counter(f"mindcore_{operation}_total")

    def record_slo_violation(self, operation: str, level: str):
        self.inc_counter(f"mindcore_{operation}_slo_violations_{level}_total")

    def set_gauge(self, name: str, value: float):
        with self._lock:
            # Gauges stored as specialised prefixed counter (3-decimal precision via round)
            self._counters[f"__gauge__{name}"] = round(value * 1000)

    def get_gauge(self, name: str) -> float:
        with self._lock:
            return self._counters.get(f"__gauge__{name}", 0) / 1000.0

    # ------------------------------------------------------------------
    # Prometheus text format
    # ------------------------------------------------------------------
    def render(self) -> str:
        """Render all metrics in Prometheus exposition format."""
        # Take atomic snapshot under lock
        with self._lock:
            uptime = time.time() - self._start_time
            counters_snapshot = dict(self._counters)
            histograms_snapshot = {k: list(v) for k, v in self._histograms.items()}

        lines = []

        # HELP/TYPE headers + data
        lines.append("# HELP mindcore_uptime_seconds Service uptime in seconds")
        lines.append("# TYPE mindcore_uptime_seconds gauge")
        lines.append(f"mindcore_uptime_seconds {uptime:.1f}")

        # Gauge helpers (use snapshot, not live lock calls)
        def _gauge_val(name: str) -> float:
            return counters_snapshot.get(f"__gauge__{name}", 0) / 1000.0

        lines.append("# HELP mindcore_memories_total Total memories in store")
        lines.append("# TYPE mindcore_memories_total gauge")
        lines.append(f"mindcore_memories_total {_gauge_val('memories_total'):.0f}")

        # Engine gauges
        for gauge_name in ("faiss_available", "embedder_available", "encryption_enabled"):
            val = _gauge_val(gauge_name)
            lines.append(f"# HELP mindcore_{gauge_name} Whether {gauge_name.replace('_', ' ')}")
            lines.append(f"# TYPE mindcore_{gauge_name} gauge")
            lines.append(f"mindcore_{gauge_name} {val:.0f}")

        # Counters
        operations = ("store", "recall", "context", "update_confidence", "delete", "stats")
        for op in operations:
            total = counters_snapshot.get(f"mindcore_{op}_total", 0)
            errors = counters_snapshot.get(f"mindcore_{op}_errors_total", 0)
            # Check violations too — they may exist independent of total/errors
            violations_present = False
            for level in ("warning", "critical"):
                if counters_snapshot.get(f"mindcore_{op}_slo_violations_{level}_total", 0) > 0:
                    violations_present = True
                    break
            if total + errors > 0 or violations_present:
                if total > 0:
                    lines.append(f"# HELP mindcore_{op}_total Total {op} operations")
                    lines.append(f"# TYPE mindcore_{op}_total counter")
                    lines.append(f"mindcore_{op}_total {total}")
                if errors > 0:
                    lines.append(f"# HELP mindcore_{op}_errors_total Total {op} errors")
                    lines.append(f"# TYPE mindcore_{op}_errors_total counter")
                    lines.append(f"mindcore_{op}_errors_total {errors}")
                for level in ("warning", "critical"):
                    v = counters_snapshot.get(f"mindcore_{op}_slo_violations_{level}_total", 0)
                    if v > 0:
                        lines.append(f"# HELP mindcore_{op}_slo_violations_{level}_total SLO violations ({level})")
                        lines.append(f"# TYPE mindcore_{op}_slo_violations_{level}_total counter")
                        lines.append(f"mindcore_{op}_slo_violations_{level}_total {v}")

        # Histograms
        for metric_name, samples in histograms_snapshot.items():
            if not samples:
                continue
            op = metric_name.replace("mindcore_", "").replace("_latency_seconds", "")
            lines.append(f"# HELP {metric_name} {op} latency distribution")
            lines.append(f"# TYPE {metric_name} histogram")
            # Build bucket counts
            sorted_samples = sorted(samples)
            total = len(sorted_samples)
            s_sum = sum(sorted_samples)
            idx = 0
            for b in self._buckets:
                while idx < total and sorted_samples[idx] <= b:
                    idx += 1
                bucket_label = "+Inf" if b == float("inf") else str(b)
                lines.append(f'{metric_name}_bucket{{le="{bucket_label}"}} {idx}')
            lines.append(f"{metric_name}_sum {s_sum:.6f}")
            lines.append(f"{metric_name}_count {total}")

        return "\n".join(lines) + "\n"


# ------------------------------------------------------------------
# Singleton
# ------------------------------------------------------------------
_collector: Optional[MetricsCollector] = None
_collector_lock = threading.Lock()


def get_collector() -> Optional[MetricsCollector]:
    """Get the global metrics collector singleton."""
    global _collector
    if _collector is None:
        with _collector_lock:
            if _collector is None:
                _collector = MetricsCollector()
    return _collector
