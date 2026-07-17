## Finding: SCALE-004 — Containerization mit Multi-Stage-Builds

**Severity:** medium
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** SCALE-004
**PDF-Reference:** Sec 5.3

### Observed Behavior / Evidence
- Profil is_cloud_deployed=true ⇒ Check anwendbar

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein Dockerfile im Repo (find: keine Treffer) — keine Multi-Stage-Builds, kein non-root USER, kein HEALTHCHECK

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)
