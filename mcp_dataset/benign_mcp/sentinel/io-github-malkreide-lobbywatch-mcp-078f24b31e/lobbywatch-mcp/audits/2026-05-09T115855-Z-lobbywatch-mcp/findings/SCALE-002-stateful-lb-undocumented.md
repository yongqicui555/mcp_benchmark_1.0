## Finding: SCALE-002 — Stateful Load Balancing für Streamable HTTP / SSE

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SCALE-002

### Observed Behavior

README dokumentiert HTTP-Deployment, aber keinen Hinweis auf sticky-session-Anforderung.

### Expected Behavior

Best-Practice-Katalog (SCALE-002). Siehe checks/SCALE-002.md für volle Pass-Criteria.

### Evidence

Kein Dockerfile/k8s-Manifest/HAProxy-Config im Repo
README.md:74-76 zeigt einfachen `LOBBYWATCH_MCP_TRANSPORT=http`-Aufruf

### Risk Description

Operatoren deployen hinter Round-Robin-LB. Mcp-Session-Id-Continuity bricht; Clients erleben sporadische Session-Drops.

### Remediation

```
Sektion 'Deployment Notes' in README.md mit: 'Cloud HTTP requires Mcp-Session-Id-aware sticky LB. See SCALE-003 for HAProxy stick-table config.'
```

### Effort Estimate

S (< 1d)
