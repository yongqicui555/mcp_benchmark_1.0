# MCP-Server Audit-Report — `bakom-mcp`

**Audit-Datum:** 2026-05-09
**Skill-Version:** 1.0.0
**Catalog-Version:** v0.5.0

---

## 1. Executive Summary

Server `bakom-mcp` wurde gegen 36 anwendbare Best-Practice-Checks geprüft. 26 bestanden, 8 Findings dokumentiert (0 critical, 0 high, 8 medium, 0 low). Production-Readiness: erreicht.

**Production-Readiness:** YES

---

## 2. Profil-Snapshot

| Feld | Wert |
|---|---|
| Server-Name | `bakom-mcp` |
| Audit-Datum | 2026-05-09 |
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
| ARCH | 8 | 0 | 3 | 0 | 0 |
| CH | 0 | 0 | 1 | 0 | 0 |
| OBS | 3 | 0 | 1 | 0 | 0 |
| OPS | 3 | 0 | 0 | 0 | 0 |
| SCALE | 0 | 0 | 0 | 1 | 0 |
| SDK | 2 | 0 | 2 | 0 | 0 |
| SEC | 10 | 0 | 1 | 1 | 0 |
| **Total** | **26** | **0** | **8** | **2** | **0** |

---

## 4. Findings-Übersicht

_Policy: `fail-or-partial`_

| ID | Category | Severity | Status |
|---|---|---|---|
| ARCH-003 | ARCH | medium | partial |
| ARCH-008 | ARCH | medium | partial |
| ARCH-012 | ARCH | medium | partial |
| CH-004 | CH | medium | partial |
| OBS-003 | OBS | medium | partial |
| SDK-002 | SDK | medium | partial |
| SDK-003 | SDK | medium | partial |
| SEC-008 | SEC | medium | partial |

**Gesamt:** 8 Findings

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
| **Audit-Datum** | 2026-05-09 |

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


### ARCH-008

# Finding: ARCH-008 — MCP-Prompts ungenutzt

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `ARCH-008` |
| **Audit-Datum** | 2026-05-09 |

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
| **Audit-Datum** | 2026-05-09 |

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
| **Audit-Datum** | 2026-05-09 |

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


### OBS-003

# Finding: OBS-003 — Strukturiertes Logging unvollständig

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open (Fortschritt: partial) |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `OBS-003` |
| **Audit-Datum** | 2026-05-09 (Re-Audit) |

### Observed Behavior

Re-Audit 2026-05-09 — partial Fortschritt aus den Phase-1/3 PRs:

- `logging.basicConfig(level=logging.INFO)` beim Modul-Import gesetzt (PR #17)
- `logger.exception()` in `_handle_api_error` und im Multi-Standort-Loop (PR #17)
- `logger.warning("Egress blocked", extra={"host": host, ...})` im Egress-Hook (PR #21)
- 3 Logger-Calls (vs. 0 im ersten Run am 2026-05-08)

Lücke: kein info-Logging pro Tool-Call (Start/Ende/Duration), kein `structlog` für JSON-Output, keine SIEM-tauglichen Felder.

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


### SDK-002

# Finding: SDK-002 — Tool-Returns sind nur `str`, keine Pydantic-Output-Modelle

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `SDK-002` |
| **Audit-Datum** | 2026-05-09 |

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
| **Audit-Datum** | 2026-05-09 |

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


### SEC-008

# Finding: SEC-008 — Keine explizite First-Run-Approval (Restrisiko, niedrig)

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | accepted-risk |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `SEC-008` |
| **Audit-Datum** | 2026-05-09 |

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


---

## 6. Remediation-Plan

### Empfohlene Reihenfolge

1. **ARCH-003** (medium, partial)
2. **ARCH-008** (medium, partial)
3. **ARCH-012** (medium, partial)
4. **CH-004** (medium, partial)
5. **OBS-003** (medium, partial)
6. **SDK-002** (medium, partial)
7. **SDK-003** (medium, partial)
8. **SEC-008** (medium, partial)

---

## 7. Audit-Metadata

| Feld | Wert |
|---|---|
| skill_version | `1.0.0` |
| catalog_version | `v0.5.0` |
| applies_when_dsl_version | `1.0` |
| policy | `fail-or-partial` |
| audit_date | `2026-05-09` |


_Generated by tools/build_report.py — do not edit by hand._
