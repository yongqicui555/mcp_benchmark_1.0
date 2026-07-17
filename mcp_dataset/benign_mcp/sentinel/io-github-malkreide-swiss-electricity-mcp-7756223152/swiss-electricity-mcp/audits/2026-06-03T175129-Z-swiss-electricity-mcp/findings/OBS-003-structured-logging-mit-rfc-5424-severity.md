## Finding: OBS-003 — Structured Logging mit RFC 5424 Severity-Stufen

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Check-Status** | fail |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `OBS-003` |
| **PDF-Reference** | Sec 6.3 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Kein Structured-Logging-Framework (structlog/loguru) in dependencies
- grep: keine Logger-Instanz im src/-Code

### Gaps / Abweichung vom Pass-Kriterium

- Ueberhaupt kein Logging vorhanden - kein JSON/logfmt, keine Severity-Stufen, kein per-Tool-Call-Context (tool name/session_id/correlation_id)

### Risk Description

MCP-Server-Logs müssen strukturiert sein (JSON oder logfmt), nicht plaintext. Das ermöglicht Aggregation in Datadog/Splunk/Loki ohne Regex-Parsing, korrelierte Suche über Correlation-IDs, und konsistente Severity-Filterung.

### Remediation

```diff
- import logging
- logger = logging.getLogger(__name__)
+ import structlog
+ logger = structlog.get_logger("mcp.server")

  @mcp.tool()
  async def search(query: str, ctx):
-     logger.info(f"Searching for {query}")
-     result = await api.search(query)
-     logger.info(f"Got {len(result)} results")
+     log = logger.bind(tool="search", query=query, session=ctx.session_id)
+     log.info("tool_invoked")
+     result = await api.search(query)
+     log.info("tool_succeeded", count=len(result))
      return result
```

### Effort Estimate

S — < 1 Tag pro Server.

### Verification After Fix

- Re-Audit von `OBS-003` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)
