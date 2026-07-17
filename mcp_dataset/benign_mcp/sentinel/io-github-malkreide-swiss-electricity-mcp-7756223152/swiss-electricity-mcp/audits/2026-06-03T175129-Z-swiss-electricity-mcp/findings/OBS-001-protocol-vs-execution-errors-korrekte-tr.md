## Finding: OBS-001 — Protocol vs. Execution Errors: korrekte Trennung

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `OBS-001` |
| **PDF-Reference** | Sec 6.1 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Anwendungsfehler werden als Exceptions geworfen und von FastMCP in isError-Tool-Results uebersetzt (UpstreamUnreachableError, server.py:496/543)
- 4xx/5xx-Differenzierung im API-Client (api_client.py:57-66)

### Gaps / Abweichung vom Pass-Kriterium

- Keine explizite isError-Behandlung im Tool-Code; Verlass auf FastMCP-Default-Wrapping
- Kein dedizierter Test fuer Protocol-Error-Pfad (falsches Tool/falsche Args) erkennbar

### Risk Description

Die MCP-Spezifikation fordert eine strikte Trennung zwischen zwei Fehler-Typen. Werden sie verwechselt, kann das LLM den Fehler nicht korrekt interpretieren und bricht in eine Halluzinations- oder Sackgassen-Schleife.

### Remediation

```diff
+ from mcp.types import TextContent
+
  @mcp.tool()
  async def query_database(query: str) -> dict:
-     # FAIL: alle Exceptions werden zu JSON-RPC-Errors
-     conn = await asyncpg.connect(DATABASE_URL)
-     return {"rows": await conn.fetch(query)}
+     try:
+         conn = await asyncpg.connect(DATABASE_URL)
+         try:
+             rows = await conn.fetch(query)
+             return {"rows": [dict(r) for r in rows]}
+         finally:
+             await conn.close()
+     except asyncpg.PostgresSyntaxError as e:
+         # Execution Error: Query-Problem ist Aufgabe des LLMs zu lösen
+         return {
+             "isError": True,
+             "content": [TextContent(
+                 type="text",
+                 text=f"SQL syntax error: {str(e)}. Try simplifying the query."
+             )],
+         }
+     except asyncpg.PostgresConnectionError:
+         # Protocol-nahe: Server ist degraded
+         raise McpError(code=-32603, message="Database temporarily unavailable")
```

### Effort Estimate

M — 1–3 Tage. Pro Tool muss der Error-Pfad reviewed werden. Bei vielen Tools (>10) entsprechend aufwändiger.

### Verification After Fix

- Re-Audit von `OBS-001` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)
