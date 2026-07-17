## Finding: SCALE-001 — Streamable HTTP für Cloud

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SCALE-001
**Verification-Status:** partial

### Observed Behavior / Evidence
- streamable-http-Transport für Cloud vorhanden (server.py:756); keine veraltete WebSocket-Implementierung

### Gaps vs. Best-Practice
- Transport-Auswahl via CLI-Flag '--http' statt ENV-Var MCP_TRANSPORT
- README dokumentiert 'MCP_TRANSPORT=sse PORT=8080' — entspricht NICHT dem Code (--http/--port)
- Kein Deployment-Manifest (railway.toml/render.yaml) das den Transport explizit setzt

### Remediation
Siehe Check `SCALE-001` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S
