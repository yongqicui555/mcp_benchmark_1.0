## Finding: SCALE-003 — Mcp-Session-Id Routing via Edge-LB (HAProxy Stick-Tables)

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SCALE-003

### Observed Behavior

Keine HAProxy-/Envoy-Beispielkonfiguration vorhanden.

### Expected Behavior

Best-Practice-Katalog (SCALE-003). Siehe checks/SCALE-003.md für volle Pass-Criteria.

### Evidence

find . -name '*.haproxy*' -o -name '*.envoy*' → 0 hits

### Risk Description

Wie SCALE-002 — Operatoren haben kein Referenzbeispiel und improvisieren.

### Remediation

```
deploy/haproxy.cfg (oder docs/) mit Stick-Table-Beispiel auf Mcp-Session-Id Header.
```

### Effort Estimate

M (1-3d)
