## Finding: ARCH-011 — Standardisierte Repo-Struktur (src-Layout, tests, README.de.md)

**Severity:** medium
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** ARCH-011
**PDF-Reference:** Anhang A8

### Observed Behavior / Evidence
- Pflicht-Files vorhanden: README.md, README.de.md, CHANGELOG.md, LICENSE, pyproject.toml
- src-Layout korrekt, tests/ und .github/workflows/ vorhanden
- CI (ci.yml) + publish.yml vorhanden; README.de.md parallel

### Gaps (Abweichung vom Best-Practice-Katalog)
- 8 Tools (>5) liegen in einer einzigen 867-Zeilen server.py ohne tools/-Aufteilung
- Abweichung von der tools/-Struktur nicht im README begründet

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)
