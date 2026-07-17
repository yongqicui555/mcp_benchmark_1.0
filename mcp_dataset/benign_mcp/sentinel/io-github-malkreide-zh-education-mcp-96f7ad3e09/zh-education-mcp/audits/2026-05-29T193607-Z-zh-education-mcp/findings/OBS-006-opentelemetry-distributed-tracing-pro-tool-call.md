## Finding: OBS-006 — OpenTelemetry Distributed Tracing pro Tool-Call

**Severity:** medium
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** OBS-006
**PDF-Reference:** Anhang B10

### Observed Behavior / Evidence
- Profil is_cloud_deployed=true ⇒ Check anwendbar

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein OpenTelemetry SDK / TracerProvider / OTLP-Exporter
- Keine Auto-Instrumentation für httpx
- Keine Spans pro Tool-Call

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)
