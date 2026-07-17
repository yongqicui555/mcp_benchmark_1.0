"""
Tests for v0.1.9 production modules: SLO, Metrics, Circuit Breaker, Retry.
"""
from __future__ import annotations

import threading
import time
import pytest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mindcore_memory.slo import SLO_TARGETS, get_slo_target, track_latency
from mindcore_memory.metrics import MetricsCollector, get_collector
from mindcore_memory.circuit_breaker import CircuitBreaker, CircuitState, CircuitOpenError, get_circuit, _circuits
from mindcore_memory.retry import retry_with_backoff, RETRYABLE_ERRORS


# =========================================================================
# SLO tests
# =========================================================================

class TestSLO:
    """Tests for SLO target definitions and track_latency decorator."""

    def test_slo_targets_all_defined(self):
        """All 6 operations + health have P95/P99 defined."""
        expected_ops = {
            "memory_store", "memory_recall", "memory_context",
            "memory_update_confidence", "memory_delete", "memory_stats",
            "health",
        }
        assert set(SLO_TARGETS.keys()) == expected_ops
        for op, targets in SLO_TARGETS.items():
            assert "p95" in targets, f"{op} missing p95"
            assert "p99" in targets, f"{op} missing p99"
            assert targets["p95"] > 0, f"{op} p95 should be > 0"
            assert targets["p99"] >= targets["p95"], f"{op} p99 < p95"

    def test_get_slo_target_known(self):
        assert get_slo_target("memory_store", "p95") == 0.050
        assert get_slo_target("memory_recall", "p99") == 0.500

    def test_get_slo_target_unknown(self):
        assert get_slo_target("nonexistent", "p95") == 0.0
        assert get_slo_target("memory_store", "p999") == 0.0

    def test_track_latency_records(self):
        """Decorator records latency in metrics collector."""
        collector = get_collector()
        # Clear any prior recordings for store
        collector._histograms.clear()

        @track_latency("memory_store")
        def fast_op():
            return 42

        result = fast_op()
        assert result == 42

        # Verify histogram recorded
        hist_key = "mindcore_memory_store_latency_seconds"
        assert hist_key in collector._histograms
        assert len(collector._histograms[hist_key]) == 1
        assert collector._histograms[hist_key][0] >= 0

    def test_track_latency_preserves_metadata(self):
        """Decorator preserves __name__ and __doc__."""
        @track_latency("memory_recall")
        def my_func():
            """My docstring."""
            pass

        assert my_func.__name__ == "my_func"
        assert my_func.__doc__ == "My docstring."

    def test_track_latency_unknown_op_no_log(self):
        """Unknown operations (p95=0) skip SLO logging — no crash."""
        collector = get_collector()
        collector._histograms.clear()

        @track_latency("nonexistent_op")
        def dummy():
            return True

        result = dummy()
        assert result is True

    def test_track_latency_exception_preserved(self):
        """Decorator re-raises exception after recording latency."""
        class MyError(Exception):
            pass

        @track_latency("memory_store")
        def failing():
            raise MyError("boom")

        with pytest.raises(MyError, match="boom"):
            failing()


# =========================================================================
# Metrics tests
# =========================================================================

class TestMetricsCollector:
    """Tests for MetricsCollector — counters, histograms, gauges, render."""

    def test_inc_counter(self):
        c = MetricsCollector()
        c.inc_counter("test_total")
        c.inc_counter("test_total", 5)
        assert c._counters["test_total"] == 6

    def test_inc_counter_thread_safe(self):
        c = MetricsCollector()
        errors = []

        def worker():
            try:
                for _ in range(1000):
                    c.inc_counter("concurrent_total")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread safety errors: {errors}"
        assert c._counters["concurrent_total"] == 10000

    def test_record_latency(self):
        c = MetricsCollector()
        c.record_latency("store", 0.001)
        c.record_latency("store", 0.005)
        assert len(c._histograms["mindcore_store_latency_seconds"]) == 2

    def test_record_latency_trims_to_10000(self):
        c = MetricsCollector()
        for i in range(15000):
            c.record_latency("store", 0.001)
        assert len(c._histograms["mindcore_store_latency_seconds"]) == 10000

    def test_record_error(self):
        c = MetricsCollector()
        c.record_error("store")
        assert c._counters["mindcore_store_errors_total"] == 1

    def test_record_success(self):
        c = MetricsCollector()
        c.record_success("recall")
        c.record_success("recall")
        assert c._counters["mindcore_recall_total"] == 2

    def test_record_slo_violation(self):
        c = MetricsCollector()
        c.record_slo_violation("store", "critical")
        assert c._counters["mindcore_store_slo_violations_critical_total"] == 1

    def test_set_and_get_gauge_precision(self):
        c = MetricsCollector()
        c.set_gauge("test_gauge", 1.5)
        assert abs(c.get_gauge("test_gauge") - 1.5) < 0.01

        c.set_gauge("test_gauge", 0.12345)
        assert abs(c.get_gauge("test_gauge") - 0.123) < 0.01  # 3-decimal

    def test_get_gauge_unknown_returns_zero(self):
        c = MetricsCollector()
        assert c.get_gauge("nonexistent") == 0.0

    def test_render_uptime(self):
        c = MetricsCollector()
        time.sleep(0.01)
        output = c.render()
        assert "mindcore_uptime_seconds" in output
        assert "TYPE mindcore_uptime_seconds gauge" in output

    def test_render_counters_when_nonzero(self):
        c = MetricsCollector()
        c.record_success("store")
        c.record_success("store")
        output = c.render()
        assert "mindcore_store_total 2" in output

    def test_render_counters_when_zero(self):
        c = MetricsCollector()
        # No operations recorded — counters section should be absent
        output = c.render()
        # But uptime and engine gauges still present
        assert "mindcore_uptime_seconds" in output

    def test_render_histogram_buckets(self):
        c = MetricsCollector()
        c.record_latency("store", 0.002)  # falls in 5ms bucket
        c.record_latency("store", 0.050)  # falls in 50ms bucket
        c.record_latency("store", 0.200)  # falls in 250ms bucket

        output = c.render()
        assert "mindcore_store_latency_seconds_bucket" in output
        assert "mindcore_store_latency_seconds_sum" in output
        assert "mindcore_store_latency_seconds_count 3" in output

    def test_render_slo_violations(self):
        c = MetricsCollector()
        c.record_slo_violation("recall", "critical")
        output = c.render()
        assert "mindcore_recall_slo_violations_critical_total" in output

    def test_render_histogram_empty(self):
        c = MetricsCollector()
        output = c.render()
        # Should not crash with empty histograms
        assert isinstance(output, str)

    def test_singleton_same_instance(self):
        c1 = get_collector()
        c2 = get_collector()
        assert c1 is c2

    def test_render_thread_safety(self):
        """Render while concurrent writes — must not crash or corrupt."""
        c = MetricsCollector()
        errors = []

        def writer():
            try:
                for i in range(500):
                    c.record_latency("store", 0.001)
                    c.inc_counter("test_total")
            except Exception as e:
                errors.append(e)

        def reader():
            try:
                for _ in range(100):
                    c.render()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer) for _ in range(4)] + \
                  [threading.Thread(target=reader) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread safety errors: {errors}"


# =========================================================================
# Circuit Breaker tests
# =========================================================================

class TestCircuitBreaker:
    """Tests for CircuitBreaker state machine."""

    def test_initial_state_closed(self):
        cb = CircuitBreaker(name="test")
        assert cb.state == CircuitState.CLOSED
        assert not cb.is_open

    def test_call_success_keeps_closed(self):
        cb = CircuitBreaker(name="test")
        result = cb.call(lambda: 42)
        assert result == 42
        assert cb.state == CircuitState.CLOSED

    def test_call_passes_args(self):
        cb = CircuitBreaker(name="test")
        result = cb.call(lambda x, y: x + y, None, 3, 4)
        assert result == 7

    def test_opens_after_failures(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)
        for i in range(3):
            with pytest.raises(ValueError):
                cb.call(lambda: exec("raise ValueError('fail')"))
        assert cb.state == CircuitState.OPEN
        assert cb.is_open

    def test_open_rejects_fast(self):
        cb = CircuitBreaker(name="test", failure_threshold=2)
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(lambda: exec("raise ValueError('fail')"))
        assert cb.state == CircuitState.OPEN
        with pytest.raises(CircuitOpenError):
            cb.call(lambda: 42)

    def test_open_uses_fallback(self):
        cb = CircuitBreaker(name="test", failure_threshold=2)
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(lambda: exec("raise ValueError('fail')"))

        result = cb.call(
            lambda: exec("raise ValueError('fail')"),
            fallback=lambda: "fallback_value"
        )
        assert result == "fallback_value"

    def test_half_open_after_timeout(self):
        cb = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.01,
        )
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(lambda: exec("raise ValueError('fail')"))
        assert cb.state == CircuitState.OPEN

        time.sleep(0.02)
        # This call transitions to half-open and should succeed
        result = cb.call(lambda: 42)
        assert result == 42
        assert cb.state == CircuitState.CLOSED

    def test_half_open_failure_reopens(self):
        cb = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.01,
        )
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(lambda: exec("raise ValueError('fail')"))
        assert cb.state == CircuitState.OPEN

        time.sleep(0.02)
        # Half-open probe fails
        with pytest.raises(ValueError):
            cb.call(lambda: exec("raise ValueError('fail again')"))
        assert cb.state == CircuitState.OPEN

    def test_half_open_max_probes(self):
        cb = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.01,
            half_open_max=1,
        )
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(lambda: exec("raise ValueError('fail')"))
        time.sleep(0.02)

        # First probe succeeds — should close circuit and not count against limit
        result = cb.call(lambda: 42)
        assert result == 42
        assert cb.state == CircuitState.CLOSED

    def test_half_open_max_probes_exceeded(self):
        """After half_open_max probes are used during the recovery window, subsequent calls are rejected."""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.05,
            half_open_max=0,  # No probes allowed
        )
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(lambda: exec("raise ValueError('fail')"))
        time.sleep(0.02)

        with pytest.raises(CircuitOpenError):
            cb.call(lambda: 42)

    def test_global_circuit_registry(self):
        # Clean up global state first
        _circuits.clear()
        cb1 = get_circuit("faiss", failure_threshold=3)
        cb2 = get_circuit("faiss")
        assert cb1 is cb2
        assert cb1.name == "faiss"
        assert cb1.failure_threshold == 3

    def test_circuit_open_error_message(self):
        cb = CircuitBreaker(name="db", failure_threshold=1, recovery_timeout=10)
        with pytest.raises(ValueError):
            cb.call(lambda: exec("raise ValueError('fail')"))
        try:
            cb.call(lambda: 42)
        except CircuitOpenError as e:
            msg = str(e)
            assert "db" in msg
            assert "OPEN" in msg


# =========================================================================
# Retry tests
# =========================================================================

class TestRetry:
    """Tests for retry_with_backoff decorator."""

    def test_success_no_retry(self):
        call_count = [0]

        @retry_with_backoff(max_retries=3, base_delay=0.001)
        def succeed():
            call_count[0] += 1
            return "ok"

        result = succeed()
        assert result == "ok"
        assert call_count[0] == 1

    def test_retry_then_succeed(self):
        call_count = [0]

        @retry_with_backoff(max_retries=3, base_delay=0.001)
        def flaky():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ConnectionError("transient")
            return "finally"

        result = flaky()
        assert result == "finally"
        assert call_count[0] == 3

    def test_retry_exhausted(self):
        @retry_with_backoff(max_retries=2, base_delay=0.001)
        def always_fail():
            raise RuntimeError("persistent")

        with pytest.raises(RuntimeError, match="persistent"):
            always_fail()

    def test_retry_non_retryable(self):
        """Non-retryable exceptions are not retried."""
        call_count = [0]

        @retry_with_backoff(max_retries=3, base_delay=0.001, retryable=(ConnectionError,))
        def type_error_func():
            call_count[0] += 1
            raise ValueError("not retryable")

        with pytest.raises(ValueError, match="not retryable"):
            type_error_func()
        assert call_count[0] == 1  # Only one attempt

    def test_retry_base_delay_increases(self):
        """Verify backoff increases delay exponentially."""
        delays = []

        # Monkey-patch time.sleep to capture delays
        original_sleep = time.sleep
        def capture_sleep(d):
            delays.append(d)
            original_sleep(0)  # Don't actually sleep

        @retry_with_backoff(max_retries=3, base_delay=0.1, backoff_factor=2.0)
        def fail_every_time():
            raise ConnectionError("fail")

        time.sleep = capture_sleep
        try:
            with pytest.raises(ConnectionError):
                fail_every_time()
        finally:
            time.sleep = original_sleep

        assert len(delays) == 3
        # Delays should increase: 0.1, 0.2, 0.4 (plus jitter)
        assert delays[0] > 0
        assert delays[1] > delays[0] * 0.8  # Rough check with jitter tolerance
        assert delays[2] > delays[1] * 0.8

    def test_retry_preserves_metadata(self):
        @retry_with_backoff(max_retries=2, base_delay=0.001)
        def my_retry_func():
            """Retry doc."""
            return True

        assert my_retry_func.__name__ == "my_retry_func"
        assert my_retry_func.__doc__ == "Retry doc."

    def test_max_delay_cap(self):
        @retry_with_backoff(max_retries=2, base_delay=5.0, max_delay=1.0)
        def fail_func():
            raise ConnectionError("fail")

        delays = []
        original_sleep = time.sleep
        def capture(d):
            delays.append(d)
            original_sleep(0)
        time.sleep = capture
        try:
            with pytest.raises(ConnectionError):
                fail_func()
        finally:
            time.sleep = original_sleep

        for d in delays:
            assert d <= 1.0 + 0.5  # max_delay + max jitter (50%)

    def test_retryable_tuple_accepts_custom_errors(self):
        class CustomTransientError(Exception):
            pass

        call_count = [0]

        @retry_with_backoff(
            max_retries=2,
            base_delay=0.001,
            retryable=(CustomTransientError,)
        )
        def custom_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise CustomTransientError("custom")
            return "ok"

        result = custom_func()
        assert result == "ok"
        assert call_count[0] == 2

    def test_default_retryable_includes_common_errors(self):
        assert TimeoutError in RETRYABLE_ERRORS
        assert ConnectionError in RETRYABLE_ERRORS
        assert OSError in RETRYABLE_ERRORS
        assert RuntimeError in RETRYABLE_ERRORS
