## Finding: OBS-003 — Structured Logging RFC 5424

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** OBS-003
**Verification-Status:** partial

### Observed Behavior / Evidence
- Kein print() im Code → kein stdout-Konflikt (Synergie OBS-004)

### Gaps vs. Best-Practice
- Kein strukturierter Logger (structlog/loguru) als Dependency; Server loggt überhaupt nicht
- Empfehlung: structlog mit JSON-Output auf sys.stderr, bound context pro Tool-Call

### Remediation
Siehe Check `OBS-003` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S
