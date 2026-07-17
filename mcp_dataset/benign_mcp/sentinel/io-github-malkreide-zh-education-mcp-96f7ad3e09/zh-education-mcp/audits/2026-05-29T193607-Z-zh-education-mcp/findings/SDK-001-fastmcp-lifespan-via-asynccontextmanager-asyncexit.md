## Finding: SDK-001 — FastMCP Lifespan via @asynccontextmanager + AsyncExitStack

**Severity:** high
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** SDK-001
**PDF-Reference:** Sec 3.1

### Observed Behavior / Evidence
- httpx.AsyncClient wird pro Request neu erzeugt (server.py:72, _http_get bei jedem Fetch aufgerufen)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Keine FastMCP lifespan/@asynccontextmanager (grep: none)
- Kein Connection-Pooling — Client pro Tool-Call statt einmalig im Lifespan
- Kein Cleanup-Pfad

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)
