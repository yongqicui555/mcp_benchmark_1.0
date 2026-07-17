## Finding: SDK-004 — CORS Mcp-Session-Id Exposure bei HTTP/SSE

**Severity:** high
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** SDK-004
**PDF-Reference:** Sec 3.1

### Observed Behavior / Evidence
- Profil Python + dual-transport ⇒ Check anwendbar; README bewirbt Browser-Zugang via claude.ai (README Cloud Deployment)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Keine CORS-Middleware konfiguriert (grep: none)
- expose_headers/allow_headers mit Mcp-Session-Id nicht gesetzt — Browser-Clients (claude.ai) brechen
- allow_origins nicht konfiguriert

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)
