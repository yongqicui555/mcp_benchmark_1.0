## Finding: SCALE-006 — Resource-Limits per Container (Memory, CPU, FDs)

**Severity:** medium
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** SCALE-006
**PDF-Reference:** Sec 5.3

### Observed Behavior / Evidence
- Profil is_cloud_deployed=true ⇒ Check anwendbar

### Gaps (Abweichung vom Best-Practice-Katalog)
- Keine Container-Resource-Limits (Memory/CPU/FD) — kein Dockerfile/k8s-Manifest vorhanden

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)
