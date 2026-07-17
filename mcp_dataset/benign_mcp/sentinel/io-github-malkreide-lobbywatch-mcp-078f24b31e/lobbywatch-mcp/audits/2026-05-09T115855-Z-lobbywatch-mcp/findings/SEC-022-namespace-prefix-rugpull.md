## Finding: SEC-022 — Tool-Hash-Pinning + Namespace-Präfix gegen Rug Pull

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SEC-022

### Observed Behavior

Tool-Namen wie `get_parlamentarier` sind nicht namespaced.

### Expected Behavior

Best-Practice-Katalog (SEC-022). Siehe checks/SEC-022.md für volle Pass-Criteria.

### Evidence

src/lobbywatch_mcp/server.py:147 async def get_parlamentarier — kein lobbywatch_-Präfix
Kollisionsrisiko mit parlament-mcp (Portfolio enthält beide)

### Risk Description

Wenn beide Server (lobbywatch-mcp + parlament-mcp) gleichzeitig laufen, kollidieren Tool-Namen oder ein bösartiger Server-Update überschreibt semantisch die Bedeutung beim Client.

### Remediation

```
Tools umbenennen: lobbywatch_get_parlamentarier, lobbywatch_list_interessenbindungen, lobbywatch_search_branche, lobbywatch_get_lobbygruppe, lobbywatch_get_ranking, lobbywatch_get_transparenzquote, lobbywatch_refresh_dump, lobbywatch_dump_status.
```

### Effort Estimate

M (1-3d)
