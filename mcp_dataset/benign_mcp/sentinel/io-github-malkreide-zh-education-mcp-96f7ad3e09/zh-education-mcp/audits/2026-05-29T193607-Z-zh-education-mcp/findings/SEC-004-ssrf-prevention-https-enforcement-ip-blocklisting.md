## Finding: SEC-004 — SSRF-Prevention: HTTPS-Enforcement + IP-Blocklisting

**Severity:** critical
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** SEC-004
**PDF-Reference:** Sec 4.4

### Observed Behavior / Evidence
- Alle ausgehenden Requests gehen an einen hartcodierten HTTPS-Host BISTA_API (server.py:32) — kein user-kontrollierter URL/Host ⇒ klassische SSRF nicht möglich
- Schema ist fix https://

### Gaps (Abweichung vom Best-Practice-Katalog)
- follow_redirects=True ohne Redirect-Host-Validierung (server.py:72) — Redirect-basierte SSRF theoretisch möglich
- Keine IP-Blocklist (169.254.169.254, loopback, link-local), keine DNS-Auflösungs-Kontrolle (TOCTOU)
- Residual-Risiko in der Praxis gering wegen fixem, vertrauenswürdigem Host

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)
