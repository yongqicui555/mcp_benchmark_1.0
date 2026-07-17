## Finding: CH-004 — OGD-CH Lizenz-Compliance

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** CH-004
**Verification-Status:** partial

### Observed Behavior / Evidence
- README nennt die Datenquelle Curia Vista (parlament.ch) und liefert Curia-Vista-Deeplink pro Treffer (server.py:399)

### Gaps vs. Best-Practice
- Keine explizite Lizenz-/Attributions-Angabe (CC BY 4.0) im README
- Tool-Antworten enthalten kein dediziertes source/license-Feld

### Remediation
Siehe Check `CH-004` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S
