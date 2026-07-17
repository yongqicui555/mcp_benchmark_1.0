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
