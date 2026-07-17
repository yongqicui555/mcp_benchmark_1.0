## Finding: OBS-006 — OpenTelemetry Distributed Tracing pro Tool-Call

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Check-Status** | fail |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `OBS-006` |
| **PDF-Reference** | Anhang B10 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- is_cloud_deployed=true -> Check anwendbar

### Gaps / Abweichung vom Pass-Kriterium

- Kein OpenTelemetry-SDK, kein TracerProvider/OTLP-Exporter
- Keine httpx-Auto-Instrumentation, keine per-Tool-Call-Spans

### Risk Description

OBS-005 deckt Audit-Logs für SIEM-Integration ab — Security-fokussiert. OBS-006 ergänzt das auf der **Performance- und Behavior-Seite**: jeder Tool-Call wird als OpenTelemetry-Span erfasst, mit:

### Remediation

### Schritt 1: SDK-Installation

```toml
# pyproject.toml
[project.dependencies]
"opentelemetry-api" = "^1.21"
"opentelemetry-sdk" = "^1.21"
"opentelemetry-exporter-otlp" = "^1.21"
"opentelemetry-instrumentation-httpx" = "^0.42b0"
```

### Schritt 2: Setup-Modul

```python
# src/server_name/observability.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
# ...

def setup_tracing():
    resource = Resource.create({
        "service.name": os.environ.get("OTEL_SERVICE_NAME", "schulamt-mcp"),
        "deployment.environment": os.environ.get("ENVIRONMENT", "development"),
    })
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    HTTPXClientInstrumentor().instrument()
```

### Schritt 3: Decorator anwenden

`@traced_tool` als Standard auf alle Tool-Decorators stacken.

### Schritt 4: OTLP-Backend wählen

Für Schulamt-Kontext: Datadog (DSG-konform mit `DD_SITE=datadoghq.eu`), Grafana Tempo (selbst-gehostet, OpenBao-Compatible), oder Honeycomb (EU-Region).

### Effort Estimate

M — 1–3 Tage. SDK-Setup + Decorator + Backend-Konfiguration + Tests.

### Verification After Fix

- Re-Audit von `OBS-006` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)
