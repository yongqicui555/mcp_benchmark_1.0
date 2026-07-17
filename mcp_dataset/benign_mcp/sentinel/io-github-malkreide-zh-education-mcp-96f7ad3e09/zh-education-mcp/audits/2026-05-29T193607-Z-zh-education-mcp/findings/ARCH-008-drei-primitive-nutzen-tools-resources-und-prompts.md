## Finding: ARCH-008 — Drei Primitive nutzen: Tools, Resources und Prompts

**Severity:** medium
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** ARCH-008
**PDF-Reference:** Anhang A2

### Observed Behavior / Evidence
- Server exponiert ausschliesslich Tools — keine Resources, keine Prompts (server.py)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Weder ≥2 Primitive genutzt noch im README begründet, warum nur Tools
- Read-only/deterministische Tools (zh_edu_list_schulgemeinden) sind Resource-Migrations-Kandidaten

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)
