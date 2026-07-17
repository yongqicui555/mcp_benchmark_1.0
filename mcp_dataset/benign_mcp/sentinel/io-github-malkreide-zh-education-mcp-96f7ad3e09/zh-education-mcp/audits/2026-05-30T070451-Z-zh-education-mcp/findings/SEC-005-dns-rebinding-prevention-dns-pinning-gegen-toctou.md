## Finding: SEC-005 — DNS-Rebinding-Prevention: DNS-Pinning gegen TOCTOU

**Severity:** high
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** SEC-005
**PDF-Reference:** Sec 4.4

### Observed Behavior / Evidence
- Single-Host-Allow-List minimiert Rebinding-Fläche (http_client.py); verify=False nicht verwendet
- Egress-Guard feuert auf jedem Hop

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein explizites DNS-IP-Pinning gegen TOCTOU — als accepted-risk in docs/accepted-risks.md dokumentiert (gering wegen Single trusted host)

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)
