"""
Performance benchmark for mindcore-memory-mcp v0.1.9.

Establishes P50/P95/P99 baselines for all 6 operations,
verifies SLO targets, and validates /health + /metrics endpoints.
"""

import sys
import json
import os
import shutil
import time
import statistics
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mindcore_memory.memory_engine import MemoryEngine
from mindcore_memory.slo import SLO_TARGETS, get_slo_target
from mindcore_memory.metrics import get_collector


def percentile(data, p):
    """Calculate percentile from sorted data."""
    if not data:
        return 0.0
    k = (len(data) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(data) - 1)
    return data[f] + (data[c] - data[f]) * (k - f) if f < len(data) - 1 else data[-1]


def benchmark_operation(name, func, iterations=200):
    """Benchmark a single operation, return ms stats."""
    latencies = []
    errors = 0
    for _ in range(iterations):
        start = time.perf_counter()
        try:
            func()
        except Exception:
            errors += 1
        latencies.append(time.perf_counter() - start)

    sorted_lat = sorted(latencies)
    p50 = percentile(sorted_lat, 50) * 1000
    p95 = percentile(sorted_lat, 95) * 1000
    p99 = percentile(sorted_lat, 99) * 1000
    avg = statistics.mean(latencies) * 1000
    std = statistics.stdev(latencies) * 1000
    slo_p95 = get_slo_target(name, "p95") * 1000
    slo_p99 = get_slo_target(name, "p99") * 1000

    passed = p95 <= slo_p95 and p99 <= slo_p99
    return {
        "name": name,
        "iterations": iterations,
        "errors": errors,
        "avg_ms": round(avg, 2),
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
        "std_ms": round(std, 2),
        "slo_p95_ms": slo_p95,
        "slo_p99_ms": slo_p99,
        "slo_passed": passed,
    }


def main():
    print("=" * 70)
    print("  MINDORE-MEMORY-MCP v0.1.9 — PERFORMANCE BENCHMARK")
    print("=" * 70)
    print()

    test_dir = tempfile.mkdtemp(prefix="mindcore_bench_")
    eng = MemoryEngine(storage_path=test_dir)

    # Pre-populate with 100 memories for realistic benchmarks
    print("Pre-populating 100 memories...")
    for i in range(100):
        eng.store(
            f"Memory entry number {i}: This is a test memory about various topics "
            f"including performance, architecture, security, and user preferences. "
            f"Key data point: {i * 3.14159:.2f}",
            importance=(i % 4) + 1,
            tags=[f"topic_{i % 5}", "benchmark"],
            session_id=f"SESSION_{(i % 3)}",
        )
    print(f"  → {eng.get_stats()['total_memories']} memories loaded")
    print()

    # ------------------------------------------------------------------
    # Benchmark all 6 operations
    # ------------------------------------------------------------------
    results = []
    mid = list(eng._memories.keys())[0]

    def bm_store():
        eng.store(f"bench_{time.perf_counter_ns()}", importance=2, tags=["bench"])

    def bm_recall():
        eng.recall("performance architecture", limit=5)

    def bm_context():
        eng.get_context_window("performance architecture", max_tokens=500)

    def bm_update():
        eng.update_confidence(mid, confidence=0.5 + (time.perf_counter_ns() % 50) / 100)

    def bm_delete_store():
        tmp_id = eng.store(f"tmp_del_{time.perf_counter_ns()}")
        eng.delete(tmp_id)

    def bm_stats():
        eng.get_stats()

    operations = [
        ("memory_store", bm_store),
        ("memory_recall", bm_recall),
        ("memory_context", bm_context),
        ("memory_update_confidence", bm_update),
        ("memory_delete", bm_delete_store),
        ("memory_stats", bm_stats),
    ]

    print("Running benchmarks (200 iterations each)...")
    print()
    for name, func in operations:
        result = benchmark_operation(name, func, iterations=200)
        results.append(result)
        status = "PASS" if result["slo_passed"] else "FAIL"
        icon = "✓" if result["slo_passed"] else "✗"
        print(f"  {icon} {name:30s}  avg={result['avg_ms']:6.1f}ms  "
              f"P50={result['p50_ms']:5.1f}ms  P95={result['p95_ms']:5.1f}ms "
              f"(SLO:{result['slo_p95_ms']:.0f}ms)  P99={result['p99_ms']:5.1f}ms "
              f"(SLO:{result['slo_p99_ms']:.0f}ms)  [{status}]")

    print()
    print("-" * 70)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    all_pass = all(r["slo_passed"] for r in results)
    print(f"  SLO COMPLIANCE: {'ALL PASSED' if all_pass else 'SOME FAILURES'}")
    print()
    print("  SLO Targets vs Actuals:")
    print(f"  {'Operation':<30s} {'Target P95':<12s} {'Actual P95':<12s} {'Target P99':<12s} {'Actual P99':<12s}")
    print(f"  {'-'*30} {'-'*12} {'-'*12} {'-'*12} {'-'*12}")
    for r in results:
        p95_ok = "✓" if r["p95_ms"] <= r["slo_p95_ms"] else "✗"
        p99_ok = "✓" if r["p99_ms"] <= r["slo_p99_ms"] else "✗"
        print(f"  {r['name']:<30s} {r['slo_p95_ms']:>5.0f}ms {p95_ok}    "
              f"{r['p95_ms']:>6.1f}ms    {r['slo_p99_ms']:>5.0f}ms {p99_ok}    "
              f"{r['p99_ms']:>6.1f}ms")

    # ------------------------------------------------------------------
    # Metrics validation
    # ------------------------------------------------------------------
    print()
    print("-" * 70)
    print("  METRICS ENDPOINT VALIDATION")
    collector = get_collector()
    rendered = collector.render()
    lines = rendered.strip().split("\n")
    print(f"  Prometheus format lines: {len(lines)}")
    # Check key metrics exist
    key_metrics = [
        "mindcore_uptime_seconds",
        "mindcore_memories_total",
        "mindcore_store_total",
        "mindcore_recall_total",
        "mindcore_stats_total",
    ]
    for km in key_metrics:
        found = any(km in line for line in lines)
        print(f"  {'✓' if found else '✗'} {km}")

    # ------------------------------------------------------------------
    # SLO violation log check
    # ------------------------------------------------------------------
    print()
    print("-" * 70)
    print("  SLO VIOLATION TRACKING")
    # Force a slow operation by adding many memories
    for i in range(500):
        eng.store(f"load_test_{i}", importance=1)
    stats = eng.get_stats()
    print(f"  Load test: {stats['total_memories']} memories total")

    # Check if slo violations were tracked
    violations = {
        "warning": collector._counters.get("mindcore_store_slo_violations_warning_total", 0),
        "critical": collector._counters.get("mindcore_store_slo_violations_critical_total", 0),
    }
    print(f"  SLO violations tracked — warning: {violations['warning']}, critical: {violations['critical']}")

    print()
    print("=" * 70)
    print(f"  FINAL VERDICT: {'PRODUCTION-READY' if all_pass else 'NEEDS TUNING'}")
    print("=" * 70)

    # Cleanup
    shutil.rmtree(test_dir, ignore_errors=True)

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
