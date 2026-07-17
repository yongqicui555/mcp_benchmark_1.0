## Finding: OBS-006 — OpenTelemetry Distributed Tracing pro Tool-Call

**Severity:** medium
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** OBS-006
**PDF-Reference:** Anhang B10

### Observed Behavior / Evidence
- Strukturierte Logs mit Latenz-Messung (ms) pro Fetch als Basis-Observability (data.py)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein OpenTelemetry/OTLP-Tracing — bewusst zurückgestellt; Logs decken den read-only Single-Backend-Fall ausreichend ab, Tracing als Folge-Härtung vorgemerkt

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)
