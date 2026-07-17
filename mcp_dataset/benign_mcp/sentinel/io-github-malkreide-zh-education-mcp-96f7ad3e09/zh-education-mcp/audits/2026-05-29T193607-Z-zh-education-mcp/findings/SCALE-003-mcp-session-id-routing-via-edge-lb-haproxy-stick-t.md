## Finding: SCALE-003 — Mcp-Session-Id Routing via Edge-LB (HAProxy Stick-Tables)

**Severity:** high
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** SCALE-003
**PDF-Reference:** Sec 5.2

### Observed Behavior / Evidence
- Profil dual + is_cloud_deployed ⇒ Check anwendbar

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein Edge-LB liest Mcp-Session-Id; keine Stick-Table/Hash-Konfig
- Kein Failover-Verhalten getestet/dokumentiert

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)
