## Finding: SDK-004 — CORS Mcp-Session-Id Exposure

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SDK-004
**Verification-Status:** partial

### Observed Behavior / Evidence
- HTTP-Transport vorhanden; primärer Use-Case stdio (Claude Desktop) und server-seitig — dort kein CORS nötig

### Gaps vs. Best-Practice
- Keine CORSMiddleware/expose_headers-Konfiguration → Browser-basierte MCP-Clients können Mcp-Session-Id nicht lesen
- Mcp-Session-Id fehlt in expose_headers; relevant sobald Browser-Clients angebunden werden

### Remediation
Siehe Check `SDK-004` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S
