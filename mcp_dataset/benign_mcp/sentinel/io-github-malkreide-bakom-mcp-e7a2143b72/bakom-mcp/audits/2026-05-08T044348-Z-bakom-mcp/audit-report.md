# MCP-Server Audit-Report — `bakom-mcp`

**Audit-Datum:** 2026-05-08
**Skill-Version:** 1.0.0
**Catalog-Version:** v0.5.0

---

## 1. Executive Summary

Server `bakom-mcp` wurde gegen 36 anwendbare Best-Practice-Checks geprüft. 15 bestanden, 19 Findings dokumentiert (3 critical, 8 high, 8 medium, 0 low). Production-Readiness: NICHT erreicht — blockierend: OBS-002, SDK-001, SDK-004, SEC-007.

**Production-Readiness:** NO

---

## 2. Profil-Snapshot

| Feld | Wert |
|---|---|
| Server-Name | `bakom-mcp` |
| Audit-Datum | 2026-05-08 |
| Skill-Version | 1.0.0 |
| Catalog-Version | v0.5.0 |
| transport | `dual` |
| auth_model | `none` |
| data_class | `Public Open Data` |
| write_capable | `False` |
| deployment | `['local-stdio', 'Docker']` |
| uses_sampling | `False` |
| tools_make_external_requests | `True` |
| stadt_zuerich_context | `False` |
| schulamt_context | `False` |
| data_source.is_swiss_open_data | `True` |

---

## 3. Applicability

### Status pro Kategorie

| Kategorie | Pass | Fail | Partial | Todo | N/A |
|---|---|---|---|---|---|
| ARCH | 7 | 0 | 4 | 0 | 0 |
| CH | 0 | 0 | 1 | 0 | 0 |
| OBS | 0 | 2 | 2 | 0 | 0 |
| OPS | 2 | 0 | 1 | 0 | 0 |
| SCALE | 0 | 0 | 0 | 1 | 0 |
| SDK | 0 | 3 | 1 | 0 | 0 |
| SEC | 6 | 1 | 4 | 1 | 0 |
| **Total** | **15** | **6** | **13** | **2** | **0** |

---

## 4. Findings-Übersicht

_Policy: `fail-or-partial`_

| ID | Category | Severity | Status |
|---|---|---|---|
| ARCH-005 | ARCH | critical | partial |
| OBS-004 | OBS | critical | partial |
| SEC-016 | SEC | critical | partial |
| OBS-001 | OBS | high | partial |
| OBS-002 | OBS | high | fail |
| OPS-001 | OPS | high | partial |
| SDK-001 | SDK | high | fail |
| SDK-004 | SDK | high | fail |
| SEC-005 | SEC | high | partial |
| SEC-007 | SEC | high | fail |
| SEC-021 | SEC | high | partial |
| ARCH-003 | ARCH | medium | partial |
| ARCH-008 | ARCH | medium | partial |
| ARCH-012 | ARCH | medium | partial |
| CH-004 | CH | medium | partial |
| OBS-003 | OBS | medium | fail |
| SDK-002 | SDK | medium | partial |
| SDK-003 | SDK | medium | fail |
| SEC-008 | SEC | medium | partial |

**Gesamt:** 19 Findings

---

## 5. Detail-Findings

### ARCH-003

# Finding: ARCH-003 — «Not Found» Anti-Pattern

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `ARCH-003` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

`_handle_api_error` (`server.py:371-385`) liefert generische Fehlermeldungen für HTTP-404, 429, 5xx, Timeout und ConnectError. Bei leeren Suchergebnissen (z.B. RTV-Suche, Antennensuche, Multi-Standort) wird eine leere Liste oder ein Hinweis ohne Heuristik zurückgegeben.

### Expected Behavior

Bei leeren Resultaten soll der Server Heuristiken anbieten: «keine Antennen im Radius 100m – möchten Sie 1000m versuchen?», «keine Sender mit Name='SRG' gefunden – meinten Sie 'SRF'?»

### Evidence

- File: `src/bakom_mcp/server.py:375` — generischer 404-Text ohne Vorschlag
- grep nach `suggest|hint|alternativ|did_you_mean`: 0 Treffer

### Risk Description

LLM-Konsumenten lassen Calls ergebnislos enden statt iterativ zu verbessern. UX-Verlust beim Anchor-Demo «Schulhäuser ohne Glasfaser».

### Remediation

```python
# Beispiel fuer Antennensuche:
if not antennen and radius < 5000:
    return {
        "treffer": [],
        "hinweis": (
            f"Keine Antennen im Radius {radius}m gefunden. "
            f"Empfehlung: Radius auf {min(radius * 2, 5000)}m erhoehen."
        ),
    }
```

### Effort Estimate

**S** — pro Tool ein 5–10-Zeilen-Block.

### Verification After Fix

Re-Audit ARCH-003 + Pytest-Test mit leerem-Resultat-Fall.


### ARCH-005

# Finding: ARCH-005 — Secret-Scan-Gaps in Repo-Hygiene

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `ARCH-005` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

Im aktuellen Code sind **keine Hardcoded Secrets** vorhanden — der Server benötigt schliesslich keine (auth_model=none, alle Datenquellen sind OGD ohne Auth). Die Risiko-Lage entsteht aber durch fehlende präventive Hygiene-Massnahmen für künftige Contributions.

### Expected Behavior

- `.gitignore` enthält `.env`, `.env.local`, `*.secrets`, `credentials*`
- `.env.example` mit Platzhaltern (Doku-Hinweis)
- CI-Workflow mit Gitleaks oder Trufflehog auf jedem PR

### Evidence

- File: `.gitignore` — kein Eintrag für `.env`/`secrets`/`credentials`
- File: `.github/workflows/ci.yml` — kein Secret-Scan-Step
- Kein `.env.example` im Repo

### Risk Description

Falls ein Contributor künftig einen API-Key (z.B. für rate-limited Premium-API von ofcomnet) hinzufügt und versehentlich `.env` committet, gibt es keine Sicherheitsnetz: kein CI-Scan, kein lokaler Pre-Commit-Hook. Public Repo + Push = sofortiger Leak.

### Remediation

```bash
# .gitignore ergaenzen:
echo "
# Secrets
.env
.env.*
!.env.example
*.secrets
credentials.json" >> .gitignore

# .env.example anlegen:
cat > .env.example <<'EOF'
# bakom-mcp benoetigt aktuell keine Secrets.
# Diese Datei ist Platzhalter fuer kuenftige optionale Konfiguration.
# Beispiel:
# OPENDATA_SWISS_API_KEY=your-key-if-rate-limited
EOF
```

CI-Workflow:

```yaml
# .github/workflows/secret-scan.yml
name: Secret Scan
on: [push, pull_request]
jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with: { fetch-depth: 0 }
      - uses: gitleaks/gitleaks-action@v2
```

### Effort Estimate

**S** — < 1 Stunde.

### Verification After Fix

Re-grep nach Secret-Patterns + CI-Run zeigt Gitleaks-Step.


### ARCH-008

# Finding: ARCH-008 — MCP-Prompts ungenutzt

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `ARCH-008` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

`@mcp.tool`: 11x, `@mcp.resource`: 2x, `@mcp.prompt`: 0x.

### Expected Behavior

MCP definiert drei Primitive (Tools, Resources, Prompts). Prompts ermöglichen wiederverwendbare LLM-Templates für häufige Use-Cases — z.B. den Anchor-Demo «Schulhäuser im Kreis 7 ohne Glasfaser».

### Evidence

- File: `src/bakom_mcp/server.py` — `grep -c '@mcp.prompt'`: 0
- README.md erwähnt Anchor-Demo, aber als Tool-Workflow, nicht als Prompt-Template

### Risk Description

Verlust an Discoverability für Endnutzer. Gut formulierte Prompt-Templates sind ein USP für Schulamt/Stadt-Zürich-Kontexte.

### Remediation

```python
@mcp.prompt(
    name="schulhaus_konnektivitaet",
    description="Vergleicht Glasfaser-Status mehrerer Schulhaeuser einer Gemeinde",
)
def schulhaus_konnektivitaet_prompt(gemeinde: str, kreis: str | None = None) -> str:
    return f"""Bitte vergleiche die Konnektivitaet (Glasfaser FTTH/FTTB) aller Schulhaeuser in {gemeinde}{f' Kreis {kreis}' if kreis else ''}.
1. Nutze bakom_multi_standort_konnektivitaet
2. Erstelle Tabelle: Name, Status, 5G-Versorgung
3. Empfiehl Priorisierung fuer Glasfaser-Ausbau."""
```

### Effort Estimate

**S** — 2–3 Prompts pro Tag.

### Verification After Fix

`grep -c '@mcp.prompt'` ≥ 1.


### ARCH-012

# Finding: ARCH-012 — protocolVersion-Pinning fehlt

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `ARCH-012` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

- pyproject.toml: `mcp[cli]>=1.3.0` — kein Upper-Bound
- `grep protocolVersion src/`: 0 Treffer
- CHANGELOG.md erwähnt MCP-Spec-Version nicht

### Expected Behavior

- Dependency mit Upper-Bound oder mindestens Version-Range, die Major-Versionsprünge verhindert
- Code-Kommentar oder Konstante `MCP_PROTOCOL_VERSION = "2025-06-18"`
- CHANGELOG-Notiz bei jedem mcp-SDK-Update

### Evidence

```toml
# pyproject.toml
dependencies = [
    "mcp[cli]>=1.3.0",  # ← kein Upper-Bound
]
```

### Risk Description

mcp-SDK 2.x wäre ein Major-Bump und könnte Breaking-Changes mit sich bringen. Aktuelles Pin lässt Pip jede Version nehmen — Reproducibility-Risiko bei späteren Installationen.

### Remediation

```toml
dependencies = [
    "mcp[cli]>=1.3.0,<2.0",
    "httpx>=0.27.0,<1.0",
    "pydantic>=2.7.0,<3.0",
]
```

Optional: `MCP_PROTOCOL_VERSION` als Konstante in `server.py` und CI-Test, der `mcp.__version__` verifiziert.

### Effort Estimate

**S** — pyproject-Edit + CHANGELOG-Note.

### Verification After Fix

Re-Audit ARCH-012, `pip install` zeigt Upper-Bound.


### CH-004

# Finding: CH-004 — OGD CC BY 4.0 Attribution unvollständig

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `CH-004` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

- README verlinkt BAKOM Open Data Portal (Zeile 281)
- Tool-Outputs enthalten `"datenquelle": "BAKOM + opendata.swiss"` (`server.py:1362`)
- Keine explizite Lizenz-Klausel in Tool-Outputs

### Expected Behavior

OGD-CH-Daten sind unter **CC BY 4.0** verfügbar. Die Lizenz verlangt:
1. Quellenangabe (Urheber: BAKOM / OFCOM)
2. Lizenz-Kennzeichnung (CC BY 4.0)
3. Link zur Lizenz-Seite

In Tool-Outputs sollte das mindestens als Footer mit-ausgegeben werden.

### Evidence

`server.py:1382`:
```python
md += "**Open Data:** https://opendata.swiss/de/organization/bundesamt-fur-kommunikation-bakom"
```

— Quelle ja, aber keine Lizenz-Erwähnung.

### Risk Description

Lizenz-Verstoss formal denkbar (gering, weil Quelle genannt). Reputationsrisiko bei Verwaltungs-Reviews. Compliance-Vermerk in Notion-Tracker erschwert ohne explizite Attribution.

### Remediation

Helper für Tool-Output-Footer:

```python
ATTRIBUTION_FOOTER = (
    "\n\n---\n"
    "**Quelle:** Bundesamt für Kommunikation (BAKOM) via opendata.swiss · "
    "**Lizenz:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.de)"
)

# Bei Markdown-Output:
md += ATTRIBUTION_FOOTER
# Bei JSON-Output:
output["lizenz"] = "CC BY 4.0"
output["lizenz_url"] = "https://creativecommons.org/licenses/by/4.0/"
```

README.md ergänzen: Sektion «Lizenz der Daten» (separat von Software-Lizenz MIT).

### Effort Estimate

**S** — 1 Helper + 11 Tool-Edit-Stellen.

### Verification After Fix

`grep "CC BY" src/bakom_mcp/server.py` ≥ 1.


### OBS-001

# Finding: OBS-001 — Protocol- vs. Execution-Errors nicht klar getrennt

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `OBS-001` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

`_handle_api_error` (`server.py:371-385`) gibt String-Returns mit `"Fehler: ..."` zurück. 34 try/except-Blöcke im File. Keine Verwendung von `McpError` oder `ToolError` aus dem mcp-SDK.

### Expected Behavior

MCP unterscheidet:
- **Protocol-Errors:** Server kaputt, Tool nicht definiert → `McpError`
- **Execution-Errors:** Tool lief, Resultat ist Fehler → Strukturierter Error-Response mit `isError: true`

### Evidence

```python
# server.py:385
return f"Fehler: Unerwarteter Fehler ({type(e).__name__}): {e}"
```

— Wird als normaler Tool-Output behandelt; LLM kann nicht unterscheiden, ob das ein Daten-Fehler oder ein Server-Crash war.

### Risk Description

LLM kann fehlerhafte Antworten nicht von leeren oder echten Antworten unterscheiden. Retry-Logik im Client greift nicht.

### Remediation

```python
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData

# Bei Tool-internen Fehlern: Tool-Error mit isError-Markierung (FastMCP):
@mcp.tool(...)
async def bakom_xxx(...) -> str:
    try:
        ...
    except httpx.HTTPStatusError as e:
        # Execution-Error: bleibt String-Return aber explicit markiert
        return _format_execution_error(e)
    except Exception as e:
        # Protocol-Error: McpError raisen
        raise McpError(ErrorData(code=-32000, message="Internal server error"))
```

### Effort Estimate

**M** — 1–2 Tage Refactor von `_handle_api_error`.

### Verification After Fix

Re-Audit OBS-001. Pytest-Test, der einen ConnectError simuliert und `isError`-Flag prüft.


### OBS-002

# Finding: OBS-002 — Roh-Exception-Details an LLM exponiert

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `OBS-002` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

```python
# server.py:385
return f"Fehler: Unerwarteter Fehler ({type(e).__name__}): {e}"

# server.py:643
"fehler": str(e)[:100],
```

Beide Stellen leiten den Exception-String direkt an das LLM weiter (nur Z. 643 mit Truncate auf 100 Zeichen).

### Expected Behavior

Generische Fehlermeldung nach aussen, Details intern in strukturierten Logs (mit Severity, Tool-Name, Request-ID).

### Evidence

- File: `src/bakom_mcp/server.py:385` — Generic-Catch-Branch im Helper
- File: `src/bakom_mcp/server.py:643` — Multi-Standort-Loop pro Standort

### Risk Description

Exception-Strings können enthalten:
- Stack-Pfade (`/home/user/...`)
- Library-Versionen (Vector für CVE-Mining)
- Interne URLs / IPs bei DNS-Fehler
- Pydantic-Validation-Errors mit Field-Snippets aus User-Input (PII unwahrscheinlich, aber möglich)

Bei Adversarial-Prompt-Injection könnten diese Strings vom LLM extrahiert werden.

### Remediation

```python
import logging
logger = logging.getLogger("bakom_mcp")

def _handle_api_error(e: Exception, *, request_id: str | None = None) -> str:
    # Detaillierte Logs intern
    logger.exception("Tool error", extra={"request_id": request_id})

    # Generische User-Message
    if isinstance(e, httpx.HTTPStatusError):
        if e.response.status_code == 404:
            return "Fehler: Ressource nicht gefunden."
        if e.response.status_code == 429:
            return "Fehler: Rate-Limit erreicht."
        return "Fehler: Externe API antwortet nicht wie erwartet."
    if isinstance(e, httpx.TimeoutException):
        return "Fehler: Zeitüberschreitung."
    if isinstance(e, httpx.ConnectError):
        return "Fehler: Verbindung zur API fehlgeschlagen."
    return "Fehler: Unerwarteter interner Fehler."  # KEIN {e} mehr

# server.py:643 ersetzen:
"fehler": "Standort konnte nicht abgefragt werden",  # statt str(e)[:100]
```

### Effort Estimate

**S** — 2 Code-Stellen + Logger-Setup.

### Verification After Fix

`grep -E 'str\(e\)|({e})' src/bakom_mcp/server.py` liefert nur noch Logger-Stellen, keine Returns.


### OBS-003

# Finding: OBS-003 — Logger definiert aber nicht verwendet

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `OBS-003` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

```python
# server.py:17, 29
import logging
logger = logging.getLogger("bakom_mcp")
```

`grep "logger\." src/bakom_mcp/server.py`: **0 Treffer.** Der Logger wird nirgends benutzt.

### Expected Behavior

Strukturiertes Logging mit RFC-5424-Severity (`debug`, `info`, `warning`, `error`, `critical`). Bei jedem Tool-Call mindestens: tool-name, status, duration, error-class.

### Evidence

- Import vorhanden, Variable initialisiert, aber kein einziger `logger.info`/`logger.error`-Call
- Keine `logging.basicConfig(...)`-Konfiguration
- Kein structlog/loguru in dependencies

### Risk Description

Bei Production-Betrieb (auch lokal stdio) keine Diagnose-Spur. Bei Fehlern muss man auf User-Reports verlassen können — keine SIEM-Integration möglich (siehe OBS-005, derzeit N/A).

### Remediation

```python
import logging
import sys
import time

# stderr fuer stdio-Server
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger("bakom_mcp")

# In Tool-Funktionen:
async def bakom_broadband_coverage(params):
    start = time.monotonic()
    logger.info("tool_call_start", extra={"tool": "bakom_broadband_coverage"})
    try:
        result = await ...
        logger.info("tool_call_ok", extra={"tool": ..., "duration_ms": (time.monotonic()-start)*1000})
        return result
    except Exception as e:
        logger.error("tool_call_failed", extra={"tool": ..., "error_class": type(e).__name__})
        return _handle_api_error(e)
```

Alternativ: `structlog` für JSON-Logs (Cloud-ready).

### Effort Estimate

**S** — basicConfig + Decorator-Pattern um alle Tools (oder Manual-Calls).

### Verification After Fix

`grep -c "logger\." src/bakom_mcp/server.py` ≥ 22 (info+error pro Tool).


### OBS-004

# Finding: OBS-004 — print()-Statement im --http-Pfad geht nach stdout

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `OBS-004` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

```python
# server.py:1752
print(f"BAKOM MCP Server läuft auf http://localhost:{port}/mcp")
```

Der Print landet auf **stdout**. Im aktuellen Code-Pfad nur bei `--http`-Flag aktiv — der stdio-Default (Z. 1755 `mcp.run()`) druckt nichts.

### Expected Behavior

Bei stdio-Servern ist **stdout reserviert für das MCP-JSON-RPC-Protokoll**. Jeder versehentliche stdout-Write bricht das Protokoll. Konvention: alle Diagnose-Outputs nach **stderr**.

### Evidence

- File: `src/bakom_mcp/server.py:1752`
- `grep "file=sys.stderr" src/bakom_mcp/server.py`: 0 Treffer

### Risk Description

Aktuell **kein direkter Bug**, weil der Print nur im `--http`-Pfad ausgeführt wird. **Risiko**: wenn ein künftiger Contributor ein Startup-Banner / Config-Dump / Debug-Info hinzufügt und dabei stdout statt stderr nutzt, bricht der stdio-Default. Konvention prophylaktisch durchsetzen.

### Remediation

```python
import sys

# server.py:1752
print(f"BAKOM MCP Server läuft auf http://localhost:{port}/mcp", file=sys.stderr)
```

Plus: Pre-Commit-Hook oder Ruff-Custom-Rule, die `print(...)` ohne `file=sys.stderr` in `src/` verbietet.

### Effort Estimate

**S** — Einzeiler-Edit + optionale Lint-Regel.

### Verification After Fix

`grep -nE "^\s*print\(" src/bakom_mcp/server.py | grep -v "file=sys.stderr"` liefert 0 Treffer.


### OPS-001

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


### SDK-001

# Finding: SDK-001 — Kein FastMCP-Lifespan, httpx-Client pro Tool-Call

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `SDK-001` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

```python
# server.py:391
mcp = FastMCP("bakom_mcp", instructions="...")
# kein lifespan-Argument

# 10x in tools:
async with httpx.AsyncClient() as client:
    ...
```

`grep "asynccontextmanager|AsyncExitStack|lifespan"`: 0 Treffer.

### Expected Behavior

FastMCP unterstützt `lifespan` als `@asynccontextmanager`. Best Practice: einen einzigen `httpx.AsyncClient` zur Server-Startup-Zeit erstellen, im Context speichern, in jedem Tool wiederverwenden.

### Evidence

- File: `src/bakom_mcp/server.py:391` — kein lifespan-Param
- File: `src/bakom_mcp/server.py:456`, 524, 600, 725, 799, 929, 1043, ... — 10 separate `async with httpx.AsyncClient()`-Blöcke

### Risk Description

- **Performance:** TLS-Handshake pro Tool-Call (~50–200ms). Bei `bakom_multi_standort_konnektivitaet` mit 20 Standorten × 2 Calls = 40 neue Connections.
- **Connection-Pool-Effekt entgeht** — httpx.AsyncClient würde HTTP/2-Connection-Reuse erlauben.
- **Lifecycle-Management:** Bei Shutdown-Signal kein graceful close.

### Remediation

```python
from contextlib import asynccontextmanager
from dataclasses import dataclass
import httpx
from mcp.server.fastmcp import FastMCP, Context

@dataclass
class AppContext:
    http: httpx.AsyncClient

@asynccontextmanager
async def lifespan(server):
    async with httpx.AsyncClient(
        timeout=15.0,
        headers={"User-Agent": "bakom-mcp/1.0"},
        http2=True,
    ) as client:
        yield AppContext(http=client)

mcp = FastMCP("bakom_mcp", instructions="...", lifespan=lifespan)

@mcp.tool(...)
async def bakom_broadband_coverage(params: BroadbandCoverageInput, ctx: Context) -> str:
    client = ctx.request_context.lifespan_context.http
    # ... statt async with httpx.AsyncClient() as client:
```

### Effort Estimate

**M** — 1–2 Tage: lifespan + Refactor von 10 Tool-Funktionen + Test-Anpassung.

### Verification After Fix

`grep -c "async with httpx.AsyncClient" src/bakom_mcp/server.py` = 0. `grep "lifespan"` ≥ 1.


### SDK-002

# Finding: SDK-002 — Tool-Returns sind nur `str`, keine Pydantic-Output-Modelle

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `SDK-002` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

Alle 11 Tool-Funktionen sind typisiert mit `-> str`. Outputs werden als Markdown- oder JSON-string zurückgegeben (`json.dumps(...)` mit `response_format`-Parameter).

### Expected Behavior

MCP-SDK serialisiert Pydantic-Models (oder TypedDicts/dataclasses) automatisch. Strukturierte Outputs lassen sich vom LLM-Client besser verarbeiten.

### Evidence

```python
# server.py:418
async def bakom_broadband_coverage(params: BroadbandCoverageInput) -> str:
    ...
    return json.dumps(output, indent=2, ensure_ascii=False)
```

Inputs nutzen Pydantic v2 mit ConfigDict — Outputs nicht.

### Risk Description

- LLM bekommt Strings, kann nicht typed-aware reasoning auf Felder
- Refactoring schwierig (kein Type-Check auf Output-Schema)
- Doku fehlt für Output-Felder im JSON-Modus

### Remediation

```python
from pydantic import BaseModel

class BroadbandCoverageOutput(BaseModel):
    standort: str
    versorgt: bool
    geschwindigkeit_mbps: int
    quelle: str = "BAKOM Breitbandatlas"
    karte_url: str

# Tool-Funktion:
async def bakom_broadband_coverage(...) -> BroadbandCoverageOutput | str:
    if params.response_format == ResponseFormat.MARKDOWN:
        return _format_markdown(...)
    return BroadbandCoverageOutput(...)
```

Alternativ: konsequent string-Returns, aber mindestens als TypedDict im JSON-Schema dokumentiert.

### Effort Estimate

**M** — 1–2 Tage für 11 Tools + Output-Modelle.

### Verification After Fix

`ast`-Check: alle `@mcp.tool`-Funktionen haben Pydantic-Return-Type oder dokumentiertes Output-Schema.


### SDK-003

# Finding: SDK-003 — Kein Context-Injection, keine Progress-Reports

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `SDK-003` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

Keine Tool-Funktion akzeptiert `Context`/`ctx`-Parameter (`grep "ctx:" src/`: 0 Treffer in tools). Dadurch kein `ctx.report_progress`, `ctx.info`, `ctx.warn`.

### Expected Behavior

Long-running Tools können Progress-Reports senden — nützlich für UI-Feedback im Claude Desktop und für Cancellation-Support.

### Evidence

- File: `src/bakom_mcp/server.py:565` — `bakom_multi_standort_konnektivitaet` läuft über bis zu 20 Standorte (= 40 HTTP-Calls), aber kein Progress-Hook.

### Risk Description

UX-Verlust: User sieht «Thinking…»-Spinner ohne Fortschritts-Indikation. Bei Timeout: kein Hinweis, wie weit der Server gekommen ist.

### Remediation

```python
from mcp.server.fastmcp import Context

@mcp.tool(...)
async def bakom_multi_standort_konnektivitaet(
    params: MultiLocationInput,
    ctx: Context,
) -> str:
    results = []
    total = len(params.locations)
    for i, loc in enumerate(params.locations):
        await ctx.report_progress(progress=i, total=total)
        await ctx.info(f"Verarbeite {loc.get('name', 'unbenannt')}")
        result = await _check_location(...)
        results.append(result)
    return json.dumps(results, ...)
```

### Effort Estimate

**S** — 1 Tag für 2–3 Long-Running-Tools.

### Verification After Fix

`grep "ctx\\.report_progress\\|ctx\\.info" src/bakom_mcp/server.py` ≥ 1.


### SDK-004

# Finding: SDK-004 — CORS / Mcp-Session-Id-Exposure ungeprüft

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `SDK-004` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

Im --http-Modus startet FastMCP einen HTTP-Server. `grep -rE "CORS|allow_origins|expose_headers|Mcp-Session-Id"` im Code: **0 Treffer.**

### Expected Behavior

Bei Streamable-HTTP / SSE muss der Server den Header `Mcp-Session-Id` für Browser-Clients explizit über `expose_headers` freigeben. Sonst kann der Client nach Reconnect die Session-ID nicht lesen.

### Evidence

- File: `src/bakom_mcp/server.py:1746-1755` — startet `mcp.run(transport="streamable-http", port=port)` ohne CORS-Konfig

### Risk Description

- **Funktionalitätsbug:** Browser-Clients können nach Reconnect nicht resumieren
- **Audit-Trail-Lücke:** Falls FastMCP-Default unsicher (z.B. `allow_origins=*`), wäre das ein CORS-Problem

Aktueller Audit ist auf Code-Ebene; Runtime-Verifikation per `curl` gegen den `--http`-Endpoint nötig.

### Remediation

Falls FastMCP's Streamable-HTTP-Default keinen Mcp-Session-Id-Expose-Header setzt, muss explizit konfiguriert werden:

```python
# Option 1: Falls FastMCP das anbietet
mcp = FastMCP(
    "bakom_mcp",
    cors_origins=["https://example.com"],   # explizit, kein "*"
    cors_expose_headers=["Mcp-Session-Id"],
)

# Option 2: Custom-ASGI-Middleware
from starlette.middleware.cors import CORSMiddleware
app = mcp.streamable_http_app()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://trusted-host.example"],
    expose_headers=["Mcp-Session-Id"],
)
```

Plus Runtime-Test:

```bash
curl -i http://localhost:8050/mcp -H "Origin: https://example.com" \
  | grep -i "Access-Control-Expose-Headers"
```

### Effort Estimate

**S** — Doku-Check + 5 Zeilen Konfig.

### Verification After Fix

`curl`-Output enthält `Access-Control-Expose-Headers: Mcp-Session-Id`.


### SEC-005

# Finding: SEC-005 — Kein DNS-Pinning (Restrisiko, niedrig)

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `SEC-005` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

URLs sind statische Konstanten (`server.py:34-47`). Keine DNS-Pinning-Logik. httpx nutzt System-DNS-Resolver mit Standard-TTL.

### Expected Behavior

Für höchste Reife: DNS-Pinning, sodass zwischen `gethostbyname()` und `connect()` kein Resolver-Wechsel den Ziel-Host austauschen kann (TOCTOU).

### Evidence

- `grep "socket.gethostbyname|getaddrinfo|dns_pin"`: 0 Treffer
- Praktisch: alle Hosts sind auf `*.admin.ch` / `opendata.swiss` / `ofcomnet.ch` — staatlich kontrolliert

### Risk Description

DNS-Rebinding-Risiko nur theoretisch:
- Kein User-controlled-Host
- Hosts unter staatlicher Kontrolle
- Risiko-Vector: Adversarial-DNS-Resolver auf der lokalen Maschine

Im stdio-Default-Setup nahezu kein Angriffs-Vektor.

### Remediation

Optional (für höhere Compliance-Anforderungen):

```python
import socket
import ssl

ALLOWED_HOSTS = {
    "api3.geo.admin.ch", "wms.geo.admin.ch", "geodesy.geo.admin.ch",
    "ckan.opendata.swiss", "opendata.swiss",
    "rtvdb.ofcomnet.ch", "www.bakom.admin.ch",
}

def _resolve_pinned(host: str) -> str:
    if host not in ALLOWED_HOSTS:
        raise ValueError(f"Host nicht in Allow-List: {host}")
    return socket.gethostbyname(host)
```

Pragmatisch: für ein Read-only-OGD-Server ist diese Massnahme **akzeptabel als Restrisiko**, dokumentieren und bei Cloud-Deploy nachrüsten.

### Effort Estimate

**S** (optional) — Egress-Allow-List bereits Voraussetzung (SEC-021).

### Verification After Fix

Falls implementiert: Test mit gefälschtem Hostname → ValueError.


### SEC-007

# Finding: SEC-007 — Kein Container-Sandboxing

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `SEC-007` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

- Kein Dockerfile im Repo
- Kein docker-compose.yml
- README dokumentiert nur uvx/pip-Install

### Expected Behavior

Ein minimaler Container (slim-bullseye / distroless) mit:
- Non-root user
- Read-only filesystem
- Egress-Limits (Network-Layer-Allow-List)
- Resource-Limits (memory, CPU)

### Evidence

- `ls Dockerfile* docker-compose*`: keine Treffer
- `grep -i docker README.md`: 0 Treffer

### Risk Description

- Bei Local-stdio-Use ist der Sandbox-Layer unverzichtbar weniger relevant (User-Trust für eigene Maschine).
- **Bei Cloud-Deployment** (HTTP-Modus): kein Container = direkter Host-Process auf der Cloud-VM = volle System-Privilegien beim Crash mit Code-Execution-CVE in Dependency.
- Anti-Shadow-MCP-Compliance (Enterprise) verlangt Container.

### Remediation

```dockerfile
# Dockerfile
FROM python:3.11-slim-bullseye AS builder
WORKDIR /build
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

FROM python:3.11-slim-bullseye
RUN useradd --uid 10001 --no-create-home --shell /sbin/nologin bakom
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY src/ /app/src/
USER bakom
ENV PYTHONPATH=/app/src
EXPOSE 8050
CMD ["python", "-m", "bakom_mcp.server", "--http"]
```

`docker-compose.yml`:

```yaml
services:
  bakom-mcp:
    build: .
    read_only: true
    cap_drop: [ALL]
    security_opt: [no-new-privileges]
    mem_limit: 256m
    cpus: 0.5
```

### Effort Estimate

**M** — 1 Tag Dockerfile + Compose + CI-Build-Job.

### Verification After Fix

`docker build .` succeeds. `docker inspect` zeigt non-root user + read_only.


### SEC-008

# Finding: SEC-008 — Keine explizite First-Run-Approval (Restrisiko, niedrig)

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | accepted-risk |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `SEC-008` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

Standard-Installation via `uvx bakom-mcp` und `claude_desktop_config.json`. Keine post-install-Scripts. Keine First-Run-Approval-Logik im Code.

### Expected Behavior

Pre-Configuration Consent: User wird vor erstem Tool-Call explizit informiert, welche externen APIs angesprochen werden, dass keine Auth erfolgt, und welche Datenkategorien zurückkommen.

### Evidence

- `grep "consent|first.run|approve" src/`: 0 Treffer
- README.md erklärt das implizit ("Open Government Data, no auth")

### Risk Description

- Gering: Server ist read-only auf Public OGD, keine PII, keine Schreib-Operation
- User-Konsens kommt ohnehin implizit über die Claude-Desktop-Tool-Approval-UI

### Remediation

**Optional** — README-Sektion «What this server does and does not» konkretisieren. Z.B.:

```markdown
## What this server does

✓ Reads BAKOM open data via three public APIs:
  - api3.geo.admin.ch (broadband / mobile coverage)
  - ckan.opendata.swiss (telecom statistics)
  - rtvdb.ofcomnet.ch (RTV database)

## What it does not

✗ Send data anywhere (read-only)
✗ Access local filesystem
✗ Use authentication tokens (none required)
✗ Cache or persist user inputs
```

Plus: First-Tool-Call kann optional einen Hinweis-Banner ausgeben (eher Anti-Pattern, daher nur Doku).

### Effort Estimate

**S** — Doku-Edit.

### Verification After Fix

README enthält «What this server does and does not»-Sektion.


### SEC-016

# Finding: SEC-016 — `host` nicht explizit gesetzt (Default-Verhalten)

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `SEC-016` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

```python
# server.py:1750-1753
port = 8050
if transport == "streamable-http":
    print(f"BAKOM MCP Server läuft auf http://localhost:{port}/mcp")
    mcp.run(transport=transport, port=port)
```

Kein `host=`-Parameter. Default kommt aus FastMCP/uvicorn-Config — typisch `127.0.0.1`, aber nicht durch Code garantiert.

### Expected Behavior

`mcp.run(host="127.0.0.1", ...)` explizit. Opt-in für `0.0.0.0` nur via Env-Var mit Warnung.

### Evidence

- `grep "0\\.0\\.0\\.0|host=" src/bakom_mcp/server.py`: keine relevanten Treffer

### Risk Description

NeighborJack: bei `0.0.0.0`-Bind hört der Server auf allen Interfaces. Auf einem geteilten Netzwerk (Coworking-WLAN, Cafés, Conference-Network) kann jeder im selben Subnet das `/mcp`-Endpoint ansprechen — ohne Auth (auth_model=none).

Aktuelles Risiko hängt vom FastMCP-Default ab. Bei künftigem SDK-Update könnte sich der Default ändern.

### Remediation

```python
import os
import sys

if transport == "streamable-http":
    host = os.environ.get("BAKOM_MCP_HOST", "127.0.0.1")
    if host == "0.0.0.0":
        print(
            "WARNUNG: Server bindet auf 0.0.0.0 (alle Interfaces). "
            "Ohne Auth ist das nur in vertrauenswürdigen Netzen sicher.",
            file=sys.stderr,
        )
    print(f"BAKOM MCP Server läuft auf http://{host}:{port}/mcp", file=sys.stderr)
    mcp.run(transport=transport, host=host, port=port)
```

### Effort Estimate

**S** — 5 Zeilen.

### Verification After Fix

```bash
ss -tlnp | grep 8050
# Expected: 127.0.0.1:8050, NICHT 0.0.0.0:8050
```


### SEC-021

# Finding: SEC-021 — Keine explizite Egress-Allow-List

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `SEC-021` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

URLs sind als Konstanten am File-Top deklariert (`server.py:34-47`). Keine User-controlled URLs. Aber: keine zentrale `ALLOWED_HOSTS`-Konstante mit Membership-Check vor jedem httpx-Call.

### Expected Behavior

Code-Layer-Allow-List als frozenset, plus Helper, der jeden Outbound-Call gegen diese Liste prüft.

### Evidence

```python
# server.py:34-47
GEO_ADMIN_API = "https://api3.geo.admin.ch/..."
OPENDATA_SWISS_API = "https://ckan.opendata.swiss/api/3/action"
RTV_DB_API = "https://rtvdb.ofcomnet.ch/api"
# ... 7+ Konstanten ohne zentrale Validierung
```

`grep "ALLOWED_HOSTS|allow_list|egress"`: 0 Treffer.

### Risk Description

- Aktuell impliziter Code-Schutz (URLs sind Konstanten, kein User-Input)
- **Future-Risiko:** Bei einem PR, der einen neuen httpx-Call mit User-controlled-URL einführt, gibt es keinen Review-Trigger
- Network-Layer fehlt komplett (Egress-Firewall) — relevant für Cloud-Deployment

### Remediation

```python
from urllib.parse import urlparse

ALLOWED_EGRESS_HOSTS: frozenset[str] = frozenset({
    "api3.geo.admin.ch",
    "wms.geo.admin.ch",
    "geodesy.geo.admin.ch",
    "ckan.opendata.swiss",
    "opendata.swiss",
    "rtvdb.ofcomnet.ch",
    "www.bakom.admin.ch",
})

async def _http_get(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    host = urlparse(url).hostname
    if host not in ALLOWED_EGRESS_HOSTS:
        raise ValueError(f"Egress-Block: {host} nicht in Allow-List")
    return await client.get(url, **kwargs)
```

Alle Tool-Funktionen migrieren auf `_http_get`. Plus pytest-Test, der einen `evil.com`-URL probiert.

### Effort Estimate

**S** — 1 Helper + Refactor von ~10 Call-Stellen.

### Verification After Fix

Pytest-Test: Tool-Aufruf mit gemockter `evil.com`-URL → `ValueError`.


---

## 6. Remediation-Plan

### Empfohlene Reihenfolge

1. **ARCH-005** (critical, partial)
2. **OBS-004** (critical, partial)
3. **SEC-016** (critical, partial)
4. **OBS-001** (high, partial)
5. **OBS-002** (high, fail)
6. **OPS-001** (high, partial)
7. **SDK-001** (high, fail)
8. **SDK-004** (high, fail)
9. **SEC-005** (high, partial)
10. **SEC-007** (high, fail)
11. **SEC-021** (high, partial)
12. **ARCH-003** (medium, partial)
13. **ARCH-008** (medium, partial)
14. **ARCH-012** (medium, partial)
15. **CH-004** (medium, partial)
16. **OBS-003** (medium, fail)
17. **SDK-002** (medium, partial)
18. **SDK-003** (medium, fail)
19. **SEC-008** (medium, partial)

---

## 7. Audit-Metadata

| Feld | Wert |
|---|---|
| skill_version | `1.0.0` |
| catalog_version | `v0.5.0` |
| applies_when_dsl_version | `1.0` |
| policy | `fail-or-partial` |
| audit_date | `2026-05-08` |


_Generated by tools/build_report.py — do not edit by hand._
