## Finding: OBS-006 — OpenTelemetry Tracing

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** OBS-006
**Verification-Status:** partial

### Observed Behavior / Evidence
- is_cloud_deployed=true → Check anwendbar

### Gaps vs. Best-Practice
- Kein OpenTelemetry-Setup (grep opentelemetry → nicht vorhanden); keine Tool-Call-Spans/Tracing
- Für Cloud-Forensik/Performance empfohlen, aber medium-Priorität

### Remediation
Siehe Check `OBS-006` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
M
