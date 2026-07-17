## Finding: SCALE-001 — Streamable HTTP statt stdio für Cloud-Deployments

**Severity:** high
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** SCALE-001
**PDF-Reference:** Sec 5.1

### Observed Behavior / Evidence
- streamable-http-Transport implementiert (server.py:863-864)
- Cloud-Deployment nutzt --http (README Render-Anleitung); keine WebSocket-Implementierung

### Gaps (Abweichung vom Best-Practice-Katalog)
- Transport-Selektion über CLI-Flag --http statt ENV-Var
- README verweist auf .../sse-Endpoint, der Code startet aber transport='streamable-http' (bedient /mcp, nicht /sse) — Endpoint-Mismatch

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)
