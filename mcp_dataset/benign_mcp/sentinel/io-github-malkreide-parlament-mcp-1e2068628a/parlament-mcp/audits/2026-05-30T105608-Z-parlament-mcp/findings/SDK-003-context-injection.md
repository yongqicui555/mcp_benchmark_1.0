## Finding: SDK-003 — Context Injection

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SDK-003
**Verification-Status:** partial

### Observed Behavior / Evidence
- Tools sind überwiegend schnelle Einzel-API-Calls (HTTP_TIMEOUT 20s)

### Gaps vs. Best-Practice
- Kein Tool deklariert ctx: Context → keine Progress-Reports/ctx.info-Logging
- Transcript-Suche kann laut README langsam sein → Progress-Reports wären sinnvoll

### Remediation
Siehe Check `SDK-003` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S
