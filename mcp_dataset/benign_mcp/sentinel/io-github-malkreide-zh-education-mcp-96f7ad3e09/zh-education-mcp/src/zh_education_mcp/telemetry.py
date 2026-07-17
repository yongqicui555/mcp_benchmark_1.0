"""OpenTelemetry-Tracing pro Tool-Call (OBS-006) — opt-in, graceful degradation.

Tracing wird **nur** aktiviert, wenn ``MCP_OTEL_ENABLED=true`` gesetzt ist UND
das ``opentelemetry``-SDK installiert ist (Extra ``[otel]``). Andernfalls ist
``traced`` ein No-Op-Decorator und der Server läuft ohne zusätzliche Abhängigkeit
— wichtig für den lokalen stdio-Default und schlanke CI.

Span-Attribute bewusst minimal (kein PII, keine freien Args-Inhalte):
``mcp.tool.name`` und ``mcp.tool.result.is_error``.
"""

from __future__ import annotations

import functools
import os
from collections.abc import Awaitable, Callable
from typing import TypeVar

from .logging_setup import log

_F = TypeVar("_F", bound=Callable[..., Awaitable[object]])

_tracer = None


def _truthy(val: str | None) -> bool:
    return (val or "").strip().lower() in ("1", "true", "yes", "on")


def setup_telemetry() -> bool:
    """Initialisiert den OTLP-Tracer, falls aktiviert und SDK verfügbar.

    Idempotent. Gibt True zurück, wenn Tracing aktiv ist.
    """
    global _tracer
    if _tracer is not None:
        return True
    if not _truthy(os.environ.get("MCP_OTEL_ENABLED")):
        return False
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        log.warning("otel_unavailable", hint="pip install 'zh-education-mcp[otel]'")
        return False

    resource = Resource.create(
        {
            "service.name": os.environ.get("OTEL_SERVICE_NAME", "zh-education-mcp"),
            "deployment.environment": os.environ.get("MCP_ENV", "production"),
        }
    )
    provider = TracerProvider(resource=resource)
    # OTLP-Endpoint via Standard-ENV (OTEL_EXPORTER_OTLP_ENDPOINT) konfigurierbar.
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)

    # Auto-Instrumentation für ausgehende httpx-Requests (Backend-Child-Spans).
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
    except ImportError:
        log.warning("otel_httpx_uninstrumented")

    _tracer = trace.get_tracer("zh_education_mcp")
    log.info("otel_enabled")
    return True


def traced(tool_name: str) -> Callable[[_F], _F]:
    """Dekoriert einen Tool-Handler mit einem OTel-Span (No-Op falls inaktiv)."""

    def decorator(fn: _F) -> _F:
        @functools.wraps(fn)
        async def wrapper(*args: object, **kwargs: object) -> object:
            if _tracer is None:
                return await fn(*args, **kwargs)
            with _tracer.start_as_current_span(f"mcp.tool/{tool_name}") as span:
                span.set_attribute("mcp.tool.name", tool_name)
                try:
                    result = await fn(*args, **kwargs)
                    span.set_attribute("mcp.tool.result.is_error", False)
                    return result
                except Exception:
                    span.set_attribute("mcp.tool.result.is_error", True)
                    raise

        return wrapper  # type: ignore[return-value]

    return decorator
