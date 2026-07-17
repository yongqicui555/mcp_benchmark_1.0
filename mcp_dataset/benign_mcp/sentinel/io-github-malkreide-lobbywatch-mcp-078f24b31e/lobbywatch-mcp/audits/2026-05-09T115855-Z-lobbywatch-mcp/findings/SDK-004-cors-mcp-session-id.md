## Finding: SDK-004 — CORS Mcp-Session-Id Exposure bei HTTP/SSE

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SDK-004

### Observed Behavior

Keine CORS-Konfiguration; Mcp-Session-Id-Header wird Browser-Clients nicht exponiert.

### Expected Behavior

Best-Practice-Katalog (SDK-004). Siehe checks/SDK-004.md für volle Pass-Criteria.

### Evidence

grep CORS|expose_headers|cors src/ → 0 hits
FastMCP-Defaults setzen Access-Control-Expose-Headers nicht für Mcp-Session-Id

### Risk Description

Browser-basierte Clients (Web-Inspector, custom UIs) verlieren Session-Continuity bei cross-origin requests; Tool-Calls schlagen sporadisch fehl.

### Remediation

```
FastMCP-Settings konfigurieren oder Starlette-Middleware hinzufügen: 
allow_origins=['https://your-app'], expose_headers=['Mcp-Session-Id']
```

### Effort Estimate

S (< 1d)
