"""
Circuit breaker — protects against cascading failures.

States: CLOSED → OPEN → HALF_OPEN → CLOSED (repeat)

Used to protect FAISS/embedding operations from repeated failures.
"""

from __future__ import annotations

import threading
import time
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional

import structlog

logger = structlog.get_logger()


class CircuitState(Enum):
    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # Failing, reject fast
    HALF_OPEN = "half_open"    # Testing recovery


class CircuitBreaker:
    """Simple circuit breaker with configurable thresholds."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max: int = 1,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max = half_open_max

        self._lock = threading.Lock()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._half_open_count = 0

    @property
    def state(self) -> CircuitState:
        with self._lock:
            return self._state

    @property
    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    def call(self, func: Callable, fallback: Optional[Callable] = None, *args: Any, **kwargs: Any) -> Any:
        """Execute func with circuit breaker protection.

        If circuit is OPEN and fallback is provided, calls fallback instead.
        If circuit is OPEN and no fallback, raises CircuitOpenError.
        """
        with self._lock:
            if self._state == CircuitState.OPEN:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_count = 0
                    logger.info("circuit_half_open", name=self.name)
                else:
                    if fallback:
                        logger.debug("circuit_open_fallback", name=self.name, remaining=round(self.recovery_timeout - elapsed, 1))
                        return fallback(*args, **kwargs)
                    raise CircuitOpenError(
                        f"Circuit '{self.name}' is OPEN. "
                        f"Retry in {round(self.recovery_timeout - elapsed, 1)}s."
                    )
            elif self._state == CircuitState.HALF_OPEN:
                if self._half_open_count >= self.half_open_max:
                    # Still in recovery timeout window — reject
                    if fallback:
                        return fallback(*args, **kwargs)
                    raise CircuitOpenError(f"Circuit '{self.name}' is in HALF_OPEN (max probes reached).")

        # Execute the protected call
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            if fallback:
                return fallback(*args, **kwargs)
            raise

    def _on_success(self):
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                logger.info("circuit_closed", name=self.name)
            self._state = CircuitState.CLOSED
            self._failure_count = 0

    def _on_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning("circuit_half_open_failed", name=self.name)
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.error("circuit_opened", name=self.name, failures=self._failure_count)


class CircuitOpenError(Exception):
    """Raised when a circuit-protected call is rejected."""
    pass


# ------------------------------------------------------------------
# Global circuit breakers
# ------------------------------------------------------------------
_circuits: dict[str, CircuitBreaker] = {}
_circuits_lock = threading.Lock()


def get_circuit(name: str, **kwargs) -> CircuitBreaker:
    """Get or create a named circuit breaker."""
    with _circuits_lock:
        if name not in _circuits:
            _circuits[name] = CircuitBreaker(name=name, **kwargs)
        return _circuits[name]
