## Finding: SEC-021 — Egress-Allow-List: Code-Layer und Network-Layer

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SEC-021

### Observed Behavior

Code-Layer-Allow-List existiert (hardcoded URLs), aber kein Network-Layer-Egress-Control.

### Expected Behavior

Best-Practice-Katalog (SEC-021). Siehe checks/SEC-021.md für volle Pass-Criteria.

### Evidence

src/lobbywatch_mcp/config.py:13-23 hardcoded URLs (gut)
Kein Proxy/Mount im httpx-Client; kein Firewall-Manifest

### Risk Description

Wenn ein DI-replaced Client (z.B. in Tests oder Fork) andere Hosts ansteuert, gibt es keine Schutzschicht.

### Remediation

```
Optional: httpx.AsyncClient(transport=AllowListTransport(['cms.lobbywatch.ch']))
Deployment-Doku: 'Container should run with NetworkPolicy egress allow-list to cms.lobbywatch.ch:443 only'.
```

### Effort Estimate

M (1-3d)
