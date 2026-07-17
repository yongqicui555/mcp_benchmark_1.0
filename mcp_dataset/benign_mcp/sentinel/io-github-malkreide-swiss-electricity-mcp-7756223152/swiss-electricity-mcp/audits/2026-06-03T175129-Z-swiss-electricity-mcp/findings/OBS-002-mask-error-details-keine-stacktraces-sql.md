## Finding: OBS-002 — Mask Error Details: keine Stacktraces / SQL ans LLM

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `OBS-002` |
| **PDF-Reference** | Sec 6.2 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Keine traceback.format_exc()/sys.exc_info()-Ausgaben in Tool-Returns
- Fehlermeldungen ohne SQL/Stacktrace

### Gaps / Abweichung vom Pass-Kriterium

- FastMCP wird nicht mit mask_error_details=True initialisiert (server.py:59)
- electricity_check_status gibt Exception-Typ+Message im note-Feld zurueck (server.py:615) - leakt Internals an Client

### Risk Description

Wenn Tool-Errors Stacktraces, SQL-Syntax, Datei-Pfade oder gar Credentials enthalten, fliesst dieser Inhalt in den LLM-Kontext und damit potentiell ins User-Sichtbare zurück. Das ist Information Disclosure: Angreifer mit User-Zugriff erfahren über provozierte Errors die Server-Architektur, DB-Schema, gemountete Pfade, sogar geleakte Tokens (z.B. in `Authorization`-Headern, die im Stacktrace landen).

### Remediation

```diff
  mcp = FastMCP(
      "server",
+     mask_error_details=True,
  )

  @mcp.tool()
  async def search(query: str):
      try:
          return await db.search(query)
-     except Exception as e:
-         return {"error": str(e), "traceback": traceback.format_exc()}
+     except UserInputError as e:
+         return {"isError": True, "content": [
+             TextContent(type="text", text=f"Invalid input: {e.user_message}")
+         ]}
+     except Exception:
+         logger.exception("Unhandled error in search tool")
+         raise  # mask_error_details greift, generische Message ans LLM
```

### Effort Estimate

S — < 1 Tag pro Server.

### Verification After Fix

- Re-Audit von `OBS-002` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)
