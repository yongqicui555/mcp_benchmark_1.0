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
