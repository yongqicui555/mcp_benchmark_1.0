"""Observability + SDK tests (audit Wave 4: OBS-001/002/003/006, SDK-003/004)."""

from __future__ import annotations

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from swiss_electricity_mcp import observability
from swiss_electricity_mcp.__main__ import build_http_app


class TestLogging:
    """OBS-003 / OBS-004."""

    def test_configure_logging_is_idempotent(self):
        observability._logging_configured = False
        observability.configure_logging()
        observability.configure_logging()  # second call must be a no-op
        assert observability._logging_configured is True

    def test_get_logger_emits_without_error(self):
        log = observability.get_logger("test")
        log.info("unit_test_event", key="value")  # must not raise


class TestTelemetry:
    """OBS-006 — tracing is opt-in via env var."""

    def test_disabled_without_endpoint(self, monkeypatch):
        monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
        observability._tracer = None
        assert observability.setup_telemetry() is None

    async def test_traced_tool_passthrough_when_disabled(self, monkeypatch):
        monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
        observability._tracer = None

        @observability.traced_tool
        async def sample(x: int) -> int:
            return x + 1

        assert await sample(41) == 42
        assert sample.__name__ == "sample"  # functools.wraps preserves identity


class TestCorsMiddleware:
    """SDK-004 — Mcp-Session-Id must be exposed/allowed, origins never wildcard."""

    def test_cors_exposes_session_id_header(self):
        app = build_http_app(origins=["https://example.com"])
        cors = [m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"]
        assert cors, "CORSMiddleware not configured"
        opts = cors[0].kwargs
        assert "Mcp-Session-Id" in opts["expose_headers"]
        assert "Mcp-Session-Id" in opts["allow_headers"]
        assert "*" not in opts["allow_origins"]

    def test_default_origins_are_empty(self):
        app = build_http_app(origins=[])
        cors = [m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"][0]
        assert cors.kwargs["allow_origins"] == []
        assert cors.kwargs["allow_credentials"] is False


class TestToolErrorPaths:
    """OBS-001 — execution and protocol error paths."""

    async def test_execution_path_happy(self):
        # Static tool, no network, no ctx — exercises the normal execution path.
        result = await mcp_call("tariff_list_categories", {})
        assert result is not None

    async def test_protocol_error_on_invalid_args(self):
        # Out-of-range argument must be rejected by schema validation.
        with pytest.raises(ToolError):
            await mcp_call("dashboard_get_consumption_forecast", {"limit_days": 99999})


async def mcp_call(name: str, args: dict):
    from swiss_electricity_mcp.server import mcp

    return await mcp.call_tool(name, args)
