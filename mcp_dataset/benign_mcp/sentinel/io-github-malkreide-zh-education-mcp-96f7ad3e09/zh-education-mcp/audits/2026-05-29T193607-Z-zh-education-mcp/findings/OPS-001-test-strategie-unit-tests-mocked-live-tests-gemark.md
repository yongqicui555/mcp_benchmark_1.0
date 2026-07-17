## Finding: OPS-001 — Test-Strategie: Unit-Tests mocked + Live-Tests gemarkert

**Severity:** high
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** OPS-001
**PDF-Reference:** Anhang C1

### Observed Behavior / Evidence
- respx-gemockte Unit-Tests vorhanden (tests/test_server.py)
- Live-Test mit @pytest.mark.live markiert; Marker in pyproject.toml registriert
- CI läuft pytest -m 'not live' (.github/workflows/ci.yml)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Nur 6 Unit-Tests gesamt statt ≥5 pro Tool (8 Tools)
- 3 Tools ohne Test: zh_edu_maturitaetsquote, zh_edu_wohnort_trend, zh_edu_mittelschulen
- Kein separater nightly/manueller Live-Test-Workflow

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)
