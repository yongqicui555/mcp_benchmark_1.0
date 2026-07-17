## Finding: SCALE-006 — Resource-Limits per Container

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SCALE-006
**Verification-Status:** partial

### Observed Behavior / Evidence
- is_cloud_deployed=true → Check anwendbar

### Gaps vs. Best-Practice
- Keine dokumentierten Resource-Limits (Memory/CPU/FD) — weder Manifest noch README
- Bei Railway via UI setzbar, sollte dokumentiert werden

### Remediation
Siehe Check `SCALE-006` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S
