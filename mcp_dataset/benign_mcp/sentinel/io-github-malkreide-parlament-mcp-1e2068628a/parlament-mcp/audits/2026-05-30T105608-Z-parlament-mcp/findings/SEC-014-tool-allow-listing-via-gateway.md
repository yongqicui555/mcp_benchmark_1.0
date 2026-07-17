## Finding: SEC-014 — Tool-Allow-Listing via Gateway

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SEC-014
**Verification-Status:** partial

### Observed Behavior / Evidence
- Einzel-Server, kein Enterprise-Gateway-Kontext; alle Tools read-only Public Data → geringe Relevanz

### Gaps vs. Best-Practice
- Keine Tool-Allow-List/Group-Checks; relevant erst im Multi-Server-Gateway-Setup

### Remediation
Siehe Check `SEC-014` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
L
