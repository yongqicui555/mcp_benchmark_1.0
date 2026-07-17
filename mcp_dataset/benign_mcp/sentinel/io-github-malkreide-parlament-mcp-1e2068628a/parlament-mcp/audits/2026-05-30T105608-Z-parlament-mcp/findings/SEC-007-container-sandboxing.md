## Finding: SEC-007 — Container-Sandboxing

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SEC-007
**Verification-Status:** partial

### Observed Behavior / Evidence
- Read-only Public-Data-Server ohne Secrets → reduzierte Angriffsfläche bei Code-Kompromittierung

### Gaps vs. Best-Practice
- Kein Dockerfile/Container-Hardening vorhanden (kein non-root USER, kein read-only FS, keine Capability-Drops)
- Empfehlung: gehärtetes Multi-Stage-Dockerfile (Synergie SCALE-004) für Cloud-Deployment

### Remediation
Siehe Check `SEC-007` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S
