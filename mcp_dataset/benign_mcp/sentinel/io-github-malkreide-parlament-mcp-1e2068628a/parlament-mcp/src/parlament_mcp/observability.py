"""OpenTelemetry Distributed Tracing pro Tool-Call (OBS-006).

Setup ist idempotent und scheitert nie hart: fehlt das OTel-SDK oder ein
Exporter, läuft der Server ohne Tracing weiter. Spans enthalten **keine** PII
(nur Tool-Name, Ergebnis-Count, Fehler-Flag).
"""

from __future__ import annotations

import os
from contextlib import contextmanager

_tracer = None
_setup_done = False


def setup_tracing(service_name: str = "parlament-mcp") -> object | None:
    """TracerProvider + httpx-Auto-Instrumentation einrichten. Idempotent."""
    global _tracer, _setup_done
    if _setup_done:
        return _tracer
    _setup_done = True

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        return None

    resource = Resource.create(
        {
            "service.name": os.environ.get("OTEL_SERVICE_NAME", service_name),
            "deployment.environment": os.environ.get("ENVIRONMENT", "development"),
        }
    )
    provider = TracerProvider(resource=resource)

    # Exporter nur, wenn ein OTLP-Endpoint konfiguriert ist.
    if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )

            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        except ImportError:
            pass

    trace.set_tracer_provider(provider)

    # Backend-API-Calls (httpx) als Child-Spans.
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
    except ImportError:
        pass

    _tracer = trace.get_tracer("parlament_mcp")
    return _tracer


@contextmanager
def tool_span(name: str, **attributes):
    """Span für einen Tool-Call. No-op, wenn kein Tracer aktiv ist."""
    if _tracer is None:
        yield None
        return
    clean = {k: v for k, v in attributes.items() if v is not None}
    with _tracer.start_as_current_span(name, attributes=clean) as span:
        yield span
