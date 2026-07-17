# Finding: OPS-001 — Test-Marker fehlen, CI-Filter ist No-Op

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `OPS-001` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

```yaml
# .github/workflows/ci.yml:46
- name: Unit-Tests
  run: pytest tests/ -m "not live"
```

Aber: `grep -rE "pytest.mark|@pytest" tests/`: **0 Treffer.** Kein Test ist mit `@pytest.mark.live` markiert. Der Filter `-m "not live"` schliesst also nichts aus → alle Tests laufen, inklusive Live-API-Calls in CI.

### Expected Behavior

- Unit-Tests mit Mocks (`pytest-mock` / `unittest.mock`) — laufen offline
- Live-Tests mit `@pytest.mark.live` — laufen lokal/nightly
- CI-Default: `pytest -m "not live"` schliesst Live-Tests effektiv aus
- `conftest.py` registriert die Marker in `pytest.ini_options`

### Evidence

- `tests/test_integration.py:4`: «Testet alle 12 Tools gegen die Live-APIs»
- `tests/conftest.py`: existiert nicht
- `pyproject.toml [tool.pytest.ini_options]`: kein `markers`-Eintrag
- `grep -r "mock" tests/`: 0 Treffer

### Risk Description

- CI-Runs sind langsam und brittle (jeder GitHub-Actions-Run hängt von 3 externen APIs ab)
- Bei API-Outage von geo.admin.ch / opendata.swiss / rtvdb.ofcomnet.ch: rote CI ohne Code-Änderung
- Rate-Limiting durch CI-Runs könnte BAKOM/opendata.swiss-APIs belasten
- Coverage-Lücken: Edge-Cases (404, 429, Timeout) werden nicht systematisch getestet

### Remediation

`pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "live: Tests against live APIs (excluded in CI)",
]
```

`tests/test_integration.py` und alle bestehenden Live-Tests:

```python
import pytest

pytestmark = pytest.mark.live  # ganzes Modul markieren

# oder pro Test:
@pytest.mark.live
async def test_breitband_zuerich():
    ...
```

Zusätzlich `tests/test_unit.py` mit Mocks:

```python
from unittest.mock import AsyncMock, patch

@patch("bakom_mcp.server.httpx.AsyncClient")
async def test_broadband_coverage_ok(mock_client):
    mock_client.return_value.__aenter__.return_value.get = AsyncMock(
        return_value=AsyncMock(json=lambda: {"results": [{"attributes": {"verfuegbar": True}}]})
    )
    result = await bakom_broadband_coverage(BroadbandCoverageInput(...))
    assert "verfügbar" in result
```

### Effort Estimate

**M** — 2–3 Tage: Marker setzen, conftest.py, ~10 Unit-Tests mit Mocks für Edge-Cases.

### Verification After Fix

```bash
pytest -m "not live" tests/  # > 0 Tests laufen
pytest -m "live" tests/       # alle bestehenden 18 Live-Tests
```

CI grün ohne externe API-Calls.
