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
