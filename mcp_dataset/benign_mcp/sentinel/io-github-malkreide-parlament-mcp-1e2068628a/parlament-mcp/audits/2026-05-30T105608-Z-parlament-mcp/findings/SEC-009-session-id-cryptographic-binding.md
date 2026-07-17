## Finding: SEC-009 — Session-ID Cryptographic Binding

**Severity:** critical
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SEC-009
**Verification-Status:** partial

### Observed Behavior / Evidence
- transport=dual → HTTP-Transport vorhanden; Session-ID-Generierung an FastMCP delegiert (kryptografisch sichere uuid4)
- Server ist read-only auf Public Open Data, kein Schreib-/Account-Zugriff

### Gaps vs. Best-Practice
- Kein kryptografisches Binding der Mcp-Session-Id an validierte User-Identität (mangels Auth nicht umsetzbar)
- Reales Hijacking-Risiko aktuell gering (keine privaten Daten, keine Write-Ops); wird kritisch, sobald Auth/PII hinzukommt

### Remediation
Siehe Check `SEC-009` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
M
