## Finding: SDK-001 — FastMCP Lifespan Management

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SDK-001
**Verification-Status:** fail

### Observed Behavior / Evidence
- Kein FastMCP-Lifespan (grep lifespan/asynccontextmanager → nicht vorhanden)
- httpx.AsyncClient wird PRO Tool-Call neu erstellt (server.py:94 und server.py:429) — exakt das Fail-Pattern des Checks

### Gaps vs. Best-Practice
- Kein Connection-Pooling → Performance-Einbusse und Leak-Gefahr bei Fehlern
- Remediation: @asynccontextmanager-Lifespan mit geteiltem httpx.AsyncClient in server.state, Cleanup im finally

### Remediation
Siehe Check `SDK-001` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S
