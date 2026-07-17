"""Optional observability layer for lobbywatch-mcp.

Closes audit findings:
    OBS-003 — Structured JSON logging with correlation IDs
    OBS-006 — OpenTelemetry distributed tracing per tool call

Both features are env-var-driven and default to *off* so the stdio
transport keeps its quiet, no-overhead behaviour. Enable for cloud /
HTTP deployments via:

    LOBBYWATCH_MCP_LOG_FORMAT=json     # structured JSON to stderr
    LOBBYWATCH_MCP_LOG_LEVEL=INFO      # DEBUG | INFO | WARNING | ERROR
    LOBBYWATCH_MCP_OTEL_ENABLED=1      # turn on tracing
    LOBBYWATCH_MCP_OTEL_ENDPOINT=...   # OTLP/HTTP collector URL (optional)

OTel itself is an *optional* runtime dependency: install with

    pip install 'lobbywatch-mcp[obs]'

If OTel is not available the tracing functions degrade to no-ops
without breaking startup.
"""

from __future__ import annotations

import contextlib
import logging
import os
import sys
import uuid
from contextvars import ContextVar
from typing import Any

import structlog

# Per-request correlation id (audit OBS-003). Bound to the structlog
# context vars on every tool entry; surfaces in every JSON log line.
correlation_id: ContextVar[str | None] = ContextVar("lobbywatch_correlation_id", default=None)


_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def configure_logging() -> None:
    """Configure logging based on env vars.

    Defaults to plain stdlib logging on stderr (preserves the audit
    OBS-004 invariant: stdio transport must never write to stdout).
    Set ``LOBBYWATCH_MCP_LOG_FORMAT=json`` to switch to structlog's
    JSON renderer with timestamps + correlation-id binding.
    """
    level_name = os.getenv("LOBBYWATCH_MCP_LOG_LEVEL", "INFO").upper()
    if level_name not in _LOG_LEVELS:
        level_name = "INFO"
    level = getattr(logging, level_name)

    fmt = os.getenv("LOBBYWATCH_MCP_LOG_FORMAT", "text").lower()

    # Bridge stdlib logging into structlog so libraries (httpx, mcp, …)
    # also emit through the chosen renderer.
    handler = logging.StreamHandler(sys.stderr)
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    if fmt == "json":
        handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                foreign_pre_chain=[
                    structlog.contextvars.merge_contextvars,
                    structlog.processors.add_log_level,
                    structlog.processors.TimeStamper(fmt="iso", utc=True),
                ],
                processors=[
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.JSONRenderer(),
                ],
            )
        )
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso", utc=True),
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(name)s %(levelname)s %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )


_otel_configured = False


def configure_tracing(service_name: str = "lobbywatch-mcp") -> bool:
    """Enable OpenTelemetry tracing if ``LOBBYWATCH_MCP_OTEL_ENABLED=1``.

    Returns True if OTel was successfully configured. Returns False (with
    a warning log) if OTel is not enabled, not installed, or the exporter
    failed to initialise — never raises so server startup is robust.

    When configured:
      * httpx outbound calls are auto-instrumented (one span per HTTP
        request, audit SEC-021 / OBS-006 traceability).
      * Tool calls become spans via ``trace_tool()`` below.
    """
    global _otel_configured

    if os.getenv("LOBBYWATCH_MCP_OTEL_ENABLED", "0") != "1":
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logging.getLogger(__name__).warning(
            "LOBBYWATCH_MCP_OTEL_ENABLED=1 but the OpenTelemetry SDK is not "
            "installed. Install the optional extra: pip install "
            "'lobbywatch-mcp[obs]'. Continuing without tracing."
        )
        return False

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    endpoint = os.getenv("LOBBYWATCH_MCP_OTEL_ENDPOINT")
    if endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )

            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        except ImportError:
            logging.getLogger(__name__).warning(
                "OTLP HTTP exporter not installed; spans will be dropped."
            )

    trace.set_tracer_provider(provider)

    # Auto-instrument httpx — one span per outbound dataIF / dump call.
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
    except ImportError:
        pass

    _otel_configured = True
    return True


@contextlib.contextmanager
def trace_tool(name: str, **attributes: Any) -> Any:
    """Context manager that creates an OTel span for a tool invocation.

    No-op when tracing is not configured — safe to wrap every tool body.
    """
    if not _otel_configured:
        yield None
        return
    try:
        from opentelemetry import trace
    except ImportError:
        yield None
        return
    tracer = trace.get_tracer("lobbywatch-mcp")
    with tracer.start_as_current_span(f"tool.{name}") as span:
        for k, v in attributes.items():
            span.set_attribute(k, v)
        yield span


def new_correlation_id() -> str:
    """Mint a new correlation id, bind it to logging context, return it.

    Called at the start of every tool invocation so subsequent log lines
    inherit it via ``structlog.contextvars.merge_contextvars``.
    """
    cid = uuid.uuid4().hex[:16]
    correlation_id.set(cid)
    structlog.contextvars.bind_contextvars(correlation_id=cid)
    return cid


def clear_correlation_id() -> None:
    """Reset request-scoped logging context (call in a ``finally``)."""
    correlation_id.set(None)
    structlog.contextvars.unbind_contextvars("correlation_id")


@contextlib.asynccontextmanager
async def observed_tool(name: str, **attributes: Any) -> Any:
    """Combined async context manager: mints a correlation id, opens an
    OTel span, and unbinds context on exit. The single wrapper for every
    tool body so OBS-003 (correlation id) and OBS-006 (tool span) stay
    in sync.
    """
    new_correlation_id()
    try:
        with trace_tool(name, **attributes):
            yield
    finally:
        clear_correlation_id()
