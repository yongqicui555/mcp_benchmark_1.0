## Finding: ARCH-012 — protocolVersion-Pinning + CHANGELOG + SDK-Update-Disziplin

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** ARCH-012

### Observed Behavior

mcp[cli]>=1.2.0 hat keinen Upper Bound; Protocol-Version wird nirgends gepinnt/geloggt.

### Expected Behavior

Best-Practice-Katalog (ARCH-012). Siehe checks/ARCH-012.md für volle Pass-Criteria.

### Evidence

pyproject.toml:40 mcp[cli]>=1.2.0

### Risk Description

Unkontrollierte SDK-Major-Bumps können Breaking Changes ohne CI-Signal einführen.

### Remediation

```
mcp[cli]>=1.2.0,<2.0.0 in pyproject.toml; logger.info("Using mcp protocolVersion=%s", PROTOCOL_VERSION) im server.py
```

### Effort Estimate

S (< 1d)
