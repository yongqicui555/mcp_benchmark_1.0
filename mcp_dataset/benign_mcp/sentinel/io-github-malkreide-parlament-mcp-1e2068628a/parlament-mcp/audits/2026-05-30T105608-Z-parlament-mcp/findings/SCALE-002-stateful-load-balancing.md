## Finding: SCALE-002 — Stateful Load Balancing

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SCALE-002
**Verification-Status:** partial

### Observed Behavior / Evidence
- Tools sind zustandslose Read-Operationen ohne Subscriptions/Per-Session-Daten → Session-Verlust bei Pod-Switch ist verlustarm

### Gaps vs. Best-Practice
- Keine Sticky-Sessions und kein Shared-State-Session-Manager (Redis) konfiguriert
- Aktuell Single-Instance-tauglich; vor horizontaler Skalierung (>1 Replica) zwingend nachzurüsten

### Remediation
Siehe Check `SCALE-002` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
M
