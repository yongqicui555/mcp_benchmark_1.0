## Finding: SCALE-002 — Stateful Load Balancing für Streamable HTTP / SSE

**Severity:** high
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** SCALE-002
**PDF-Reference:** Sec 5.2

### Observed Behavior / Evidence
- Profil dual-transport ⇒ Check anwendbar

### Gaps (Abweichung vom Best-Practice-Katalog)
- Keine Sticky-Sessions / kein Shared-State-Session-Manager (Redis o.ä.) konfiguriert
- Keine Session-TTL definiert
- Kein Deployment-Manifest mit LB-Affinity

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)
