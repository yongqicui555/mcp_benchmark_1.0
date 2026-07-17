## Finding: ARCH-009 — Tool Annotations: readOnlyHint, destructiveHint, idempotentHint, openWorldHint

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** ARCH-009

### Observed Behavior

Keine der 8 Tools deklariert MCP Tool Annotations.

### Expected Behavior

Best-Practice-Katalog (ARCH-009). Siehe checks/ARCH-009.md für volle Pass-Criteria.

### Evidence

src/lobbywatch_mcp/server.py:146-401: alle @mcp.tool() ohne annotations=...

### Risk Description

Clients können nicht erkennen welche Tools sicher / read-only / external-data sind. UI-Hinweise (z.B. Confirmation-Prompts vor destructive Tools) fehlen.

### Remediation

```
@mcp.tool(annotations={'readOnlyHint': True, 'openWorldHint': False})
async def get_parlamentarier(...): ...

# refresh_dump → idempotentHint=True (re-running yields same cache state)
# get_lobbygruppe → openWorldHint=True (live external data)
```

### Effort Estimate

S (< 1d)
