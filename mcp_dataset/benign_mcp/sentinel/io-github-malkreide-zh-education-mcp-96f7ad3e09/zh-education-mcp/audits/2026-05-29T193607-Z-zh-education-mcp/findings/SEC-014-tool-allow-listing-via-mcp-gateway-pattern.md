## Finding: SEC-014 — Tool-Allow-Listing via MCP-Gateway-Pattern

**Severity:** medium
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** SEC-014
**PDF-Reference:** Sec 5.3

### Observed Behavior / Evidence
- Profil is_cloud_deployed=true ⇒ Check anwendbar

### Gaps (Abweichung vom Best-Practice-Katalog)
- Keine Tool-Allow-List / kein default-deny / kein MCP-Gateway
- Geringe Priorität: standalone, read-only, öffentliche Daten — Gateway-Pattern ist eher Portfolio-Ebene

### Effort Estimate
L  (S < 1d · M 1-3d · L 1-2w · XL >2w)
