## Finding: OBS-006 — OpenTelemetry Distributed Tracing pro Tool-Call

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `OBS-006` |
| **PDF-Reference** | Sec 6.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- No OpenTelemetry SDK in dependencies; no tracer/exporter setup in src/

### Gaps vs. Pass Criteria

- No distributed tracing, no per-tool-call spans, no httpx auto-instrumentation — relevant for the cloud (Render) deployment target

### Expected Behavior

OTel SDK + OTLP exporter, httpx auto-instrumentation, one span per tool call (mcp.tool.name, is_error), OTLP endpoint via env var, no sensitive data in attributes.

### Risk Description

No tracing means upstream latency (SIKART/SNM/NB) and cross-search fan-out cannot be observed in production; slow-source diagnosis is guesswork.

### Remediation

Add opentelemetry-sdk + opentelemetry-instrumentation-httpx; wrap each tool body in a span; configure the OTLP endpoint via `OTEL_EXPORTER_OTLP_ENDPOINT`; set service.name + environment. Gate it behind the env var so stdio/local stays zero-overhead.

### Effort Estimate

**M**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `OBS-006` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.
