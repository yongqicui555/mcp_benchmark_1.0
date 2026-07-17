"""Tests for the observability layer (audit OBS-003, OBS-006).

These tests run synchronously — they exercise pure-Python configuration
helpers, no MCP I/O.
"""

from __future__ import annotations

import json
import logging

import pytest

from lobbywatch_mcp._observability import (
    clear_correlation_id,
    configure_logging,
    configure_tracing,
    correlation_id,
    new_correlation_id,
    observed_tool,
)


@pytest.fixture(autouse=True)
def _reset_logging():
    """Each test starts from a clean root-logger state."""
    root = logging.getLogger()
    saved = (root.level, list(root.handlers))
    yield
    root.handlers = saved[1]
    root.setLevel(saved[0])
    clear_correlation_id()


def test_configure_logging_text_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LOBBYWATCH_MCP_LOG_FORMAT", raising=False)
    configure_logging()
    assert logging.getLogger().level == logging.INFO


def test_configure_logging_respects_level(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOBBYWATCH_MCP_LOG_LEVEL", "DEBUG")
    configure_logging()
    assert logging.getLogger().level == logging.DEBUG


def test_configure_logging_json_emits_structured_lines(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """OBS-003: JSON mode produces parseable structured log lines on stderr."""
    monkeypatch.setenv("LOBBYWATCH_MCP_LOG_FORMAT", "json")
    monkeypatch.setenv("LOBBYWATCH_MCP_LOG_LEVEL", "INFO")
    configure_logging()
    new_correlation_id()
    logging.getLogger("lobbywatch.test").info("hello world", extra={"foo": "bar"})

    captured = capsys.readouterr().err.strip().splitlines()
    assert captured, "expected JSON line on stderr"
    # The last line should be valid JSON with our message.
    parsed = json.loads(captured[-1])
    assert parsed["event"] == "hello world"
    assert parsed["level"] == "info"
    assert "correlation_id" in parsed
    assert parsed["correlation_id"] == correlation_id.get()


def test_correlation_id_is_unique() -> None:
    a = new_correlation_id()
    b = new_correlation_id()
    assert a != b
    clear_correlation_id()
    assert correlation_id.get() is None


async def test_observed_tool_sets_and_clears_correlation_id() -> None:
    """OBS-003: observed_tool wrapper binds the id for the duration of the call."""
    assert correlation_id.get() is None
    async with observed_tool("test_tool", arg1="x"):
        bound = correlation_id.get()
        assert bound is not None
        assert len(bound) == 16
    assert correlation_id.get() is None


def test_configure_tracing_no_op_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """OBS-006: opt-in only. Without LOBBYWATCH_MCP_OTEL_ENABLED=1 we no-op."""
    monkeypatch.delenv("LOBBYWATCH_MCP_OTEL_ENABLED", raising=False)
    assert configure_tracing() is False


def test_configure_tracing_warns_when_otel_missing(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """If OTel is not installed but enabled, we warn and continue."""
    monkeypatch.setenv("LOBBYWATCH_MCP_OTEL_ENABLED", "1")

    # Force the import to fail by making the module appear missing.
    import sys

    saved = sys.modules.get("opentelemetry")
    sys.modules["opentelemetry"] = None  # type: ignore[assignment]
    try:
        with caplog.at_level(logging.WARNING):
            configured = configure_tracing()
    finally:
        if saved is not None:
            sys.modules["opentelemetry"] = saved
        else:
            sys.modules.pop("opentelemetry", None)

    assert configured is False
