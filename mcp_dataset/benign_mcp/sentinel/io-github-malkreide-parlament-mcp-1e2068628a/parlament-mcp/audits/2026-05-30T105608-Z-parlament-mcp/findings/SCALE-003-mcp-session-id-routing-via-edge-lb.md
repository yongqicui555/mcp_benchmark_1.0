## Finding: SCALE-003 — Mcp-Session-Id Routing via Edge-LB

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SCALE-003
**Verification-Status:** partial

### Observed Behavior / Evidence
- Kein Mehr-Replica-Betrieb erkennbar; Single-Instance benötigt kein Edge-LB-Session-Routing

### Gaps vs. Best-Practice
- Keine HAProxy/NGINX/Ingress-Konfiguration für Mcp-Session-Id-Routing vorhanden
- Vor Skalierung gemeinsam mit SCALE-002 umzusetzen

### Remediation
Siehe Check `SCALE-003` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
M
