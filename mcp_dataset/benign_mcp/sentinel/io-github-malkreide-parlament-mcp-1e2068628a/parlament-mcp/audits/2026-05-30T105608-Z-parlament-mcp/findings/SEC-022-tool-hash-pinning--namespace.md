## Finding: SEC-022 — Tool-Hash-Pinning + Namespace

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SEC-022
**Verification-Status:** partial

### Observed Behavior / Evidence
- Konsistenter Namespace-Präfix 'parlament_' auf allen 6 Tools (server.py) → Cross-Server-Tool-Shadowing verhindert

### Gaps vs. Best-Practice
- Kein Tool-Definitions-Hash-Snapshot im Release-Workflow (Rug-Pull-Detection fehlt)
- CHANGELOG nennt keine Tool-Definition-Hashes/Änderungen

### Remediation
Siehe Check `SEC-022` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
M
