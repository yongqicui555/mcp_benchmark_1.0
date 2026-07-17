## Finding: OPS-001 — Test-Strategie

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** OPS-001
**Verification-Status:** partial

### Observed Behavior / Evidence
- @pytest.mark.live-Marker genutzt + in pyproject registriert (pyproject.toml:59-61, tests/test_server.py:173)
- CI läuft 'pytest -m "not live"' (.github/workflows/ci.yml)
- Unit-Tests mit gemockten HTTP-Antworten (unittest.mock patch von _odata_get)

### Gaps vs. Best-Practice
- Nur ~3-4 von 6 Tools haben Unit-Tests (get_business, get_votes, get_transcripts ohne Test)
- respx ist Dev-Dependency, wird aber nicht genutzt (mock.patch statt respx)
- Kein separater nightly/manueller Live-Test-Workflow

### Remediation
Siehe Check `OPS-001` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
M
