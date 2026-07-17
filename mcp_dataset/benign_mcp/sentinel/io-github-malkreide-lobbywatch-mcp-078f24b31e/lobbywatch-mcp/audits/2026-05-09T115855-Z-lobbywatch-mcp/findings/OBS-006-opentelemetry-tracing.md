## Finding: OBS-006 — OpenTelemetry Distributed Tracing pro Tool-Call

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** OBS-006

### Observed Behavior

Keine OTel-Instrumentation.

### Expected Behavior

Best-Practice-Katalog (OBS-006). Siehe checks/OBS-006.md für volle Pass-Criteria.

### Evidence

grep opentelemetry|otel src/ pyproject.toml → 0 hits

### Risk Description

Performance-Probleme im Tool-Pipeline (Dump-Parse, Fuzzy-Match, dataIF-Live-Call) sind ohne Tracing schwer zu lokalisieren.

### Remediation

```
opentelemetry-api + opentelemetry-instrumentation-httpx; Span pro Tool-Call mit tool_name als Attribute.
```

### Effort Estimate

M (1-3d)
