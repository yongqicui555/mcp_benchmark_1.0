"""Structured logging (OBS-003/004) and OpenTelemetry tracing (OBS-006).

Logging is JSON to **stderr** — never stdout, which is reserved for the stdio
JSON-RPC channel. Tracing is opt-in: it activates only when
``OTEL_EXPORTER_OTLP_ENDPOINT`` is set and the ``otel`` extra is installed;
otherwise every helper here is a cheap no-op.
"""

from __future__ import annotations

import functools
import logging
import os
import sys
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

import structlog

SERVICE_NAME = "swiss-electricity-mcp"

_logging_configured = False
_tracer: Any | None = None  # opentelemetry Tracer when enabled, else None


def configure_logging(level: str | None = None) -> None:
    """Configure structlog to emit JSON to stderr. Idempotent."""
    global _logging_configured
    if _logging_configured:
        return
    level_name = (level or os.environ.get("SWISS_ELECTRICITY_LOG_LEVEL", "INFO")).upper()
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelNamesMapping().get(level_name, logging.INFO)
        ),
        # stderr only: stdout is the stdio transport channel (OBS-004).
        logger_factory=structlog.WriteLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )
    _logging_configured = True


def get_logger(name: str = SERVICE_NAME) -> Any:
    """Return a bound structlog logger (configuring logging on first use)."""
    if not _logging_configured:
        configure_logging()
    return structlog.get_logger(name)


def setup_telemetry() -> Any | None:
    """Set up OTLP tracing + httpx auto-instrumentation if configured.

    Returns the tracer when enabled, else None. Enabled iff
    ``OTEL_EXPORTER_OTLP_ENDPOINT`` is set and the ``otel`` extra is installed.
    """
    global _tracer
    if _tracer is not None:
        return _tracer
    if not os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return None
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        get_logger().warning(
            "otel_requested_but_not_installed",
            hint="install the 'otel' extra: pip install 'swiss-electricity-mcp[otel]'",
        )
        return None

    resource = Resource.create(
        {
            "service.name": SERVICE_NAME,
            "deployment.environment": os.environ.get(
                "SWISS_ELECTRICITY_ENV", "unknown"
            ),
        }
    )
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    HTTPXClientInstrumentor().instrument()
    _tracer = trace.get_tracer(SERVICE_NAME)
    get_logger().info("otel_enabled", endpoint=os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"])
    return _tracer


def shutdown_telemetry() -> None:
    """Flush and shut down the tracer provider (called on server shutdown)."""
    global _tracer
    if _tracer is None:
        return
    try:
        from opentelemetry import trace

        provider = trace.get_tracer_provider()
        shutdown = getattr(provider, "shutdown", None)
        if callable(shutdown):
            shutdown()
    finally:
        _tracer = None


F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def traced_tool(func: F) -> F:
    """Wrap an async tool so each call is one span: ``mcp.tool.<name>``.

    No-op overhead when tracing is disabled. Records ``mcp.tool.name`` and
    ``mcp.tool.result.is_error``; never records raw argument values (no PII /
    free-form content in span attributes — OBS-006).
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        tracer = setup_telemetry()
        if tracer is None:
            return await func(*args, **kwargs)
        with tracer.start_as_current_span(f"mcp.tool.{func.__name__}") as span:
            span.set_attribute("mcp.tool.name", func.__name__)
            try:
                result = await func(*args, **kwargs)
            except Exception:
                span.set_attribute("mcp.tool.result.is_error", True)
                raise
            span.set_attribute("mcp.tool.result.is_error", False)
            return result

    return wrapper  # type: ignore[return-value]
