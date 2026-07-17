## Finding: SEC-021 — Egress-Allow-List

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SEC-021
**Verification-Status:** partial

### Observed Behavior / Evidence
- De-facto Single-Host-Egress: Code kontaktiert ausschliesslich die hartcodierte BASE_URL ws.parlament.ch

### Gaps vs. Best-Practice
- Keine explizite Code-Layer Allow-List (frozenset) mit assert_host_allowed-Check
- Keine Network-Layer-Egress-Control (NetworkPolicy/Security Group)
- Keine docs/network-egress.md — reales Risiko gering (keine user-kontrollierten URLs)

### Remediation
Siehe Check `SEC-021` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
M
