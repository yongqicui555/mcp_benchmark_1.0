## Finding: SCALE-004 — Containerization mit Multi-Stage-Builds

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SCALE-004
**Verification-Status:** partial

### Observed Behavior / Evidence
- is_cloud_deployed=true → Check anwendbar

### Gaps vs. Best-Practice
- Kein Dockerfile vorhanden — kein Multi-Stage-Build, kein non-root USER, kein HEALTHCHECK
- Empfehlung: schlankes Multi-Stage-Dockerfile (Synergie SEC-007)

### Remediation
Siehe Check `SCALE-004` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S
