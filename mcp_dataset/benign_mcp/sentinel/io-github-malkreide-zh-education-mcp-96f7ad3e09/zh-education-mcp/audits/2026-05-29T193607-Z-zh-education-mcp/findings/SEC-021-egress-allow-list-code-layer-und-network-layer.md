## Finding: SEC-021 — Egress-Allow-List: Code-Layer und Network-Layer

**Severity:** high
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** SEC-021
**PDF-Reference:** Anhang B5 + B12

### Observed Behavior / Evidence
- De-facto Single-Host-Egress: alle Requests gehen an hartcodiertes BISTA_API (server.py:32)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Keine erzwungene Code-Layer-Allow-List (frozenset) und kein assert_host_allowed vor Requests
- Keine Network-Layer-Egress-Kontrolle dokumentiert
- follow_redirects=True kann den impliziten Single-Host umgehen

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)
