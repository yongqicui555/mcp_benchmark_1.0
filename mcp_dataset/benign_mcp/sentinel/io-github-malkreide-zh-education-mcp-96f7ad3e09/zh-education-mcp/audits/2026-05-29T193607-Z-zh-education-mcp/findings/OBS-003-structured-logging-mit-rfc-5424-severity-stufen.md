## Finding: OBS-003 — Structured Logging mit RFC 5424 Severity-Stufen

**Severity:** medium
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** OBS-003
**PDF-Reference:** Sec 6.3

### Observed Behavior / Evidence
- Kein print() im src/ (gut für stdio)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein structured Logger (structlog/loguru) in dependencies
- Kein JSON/logfmt-Logging, keine Severity-Stufen, keine correlation_id/session-Bindung
- Tool-Calls werden überhaupt nicht geloggt

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)
