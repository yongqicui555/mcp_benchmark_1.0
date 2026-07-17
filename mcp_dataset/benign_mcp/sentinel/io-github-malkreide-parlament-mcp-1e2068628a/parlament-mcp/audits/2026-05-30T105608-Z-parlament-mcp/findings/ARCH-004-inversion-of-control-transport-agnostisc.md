## Finding: ARCH-004 — Inversion of Control: Transport-agnostische Logik

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** ARCH-004
**Verification-Status:** partial

### Observed Behavior / Evidence
- Tool-Handler greifen nicht auf Transport-Internals (request.headers etc.) zu — rein Pydantic-Input-Modelle
- Dual-Transport unterstützt: stdio (Default) + streamable-http (server.py:751-758)

### Gaps vs. Best-Practice
- Keine Settings/BaseSettings — Konfiguration über Modul-Konstanten + sys.argv
- Transport-Auswahl via CLI-Flag '--http' statt ENV-Var; README behauptet MCP_TRANSPORT=sse, was der Code NICHT implementiert (Doku/Code-Mismatch)
- Kein gemeinsamer Lifespan-Setup

### Remediation
Siehe Check `ARCH-004` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
M
