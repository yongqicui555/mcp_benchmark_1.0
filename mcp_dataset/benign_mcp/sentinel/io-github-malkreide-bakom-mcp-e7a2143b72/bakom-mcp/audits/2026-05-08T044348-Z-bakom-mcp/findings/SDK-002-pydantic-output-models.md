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
