## Finding: SCALE-004 — Containerization mit Multi-Stage-Builds

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SCALE-004

### Observed Behavior

Kein Dockerfile.

### Expected Behavior

Best-Practice-Katalog (SCALE-004). Siehe checks/SCALE-004.md für volle Pass-Criteria.

### Evidence

find . -name 'Dockerfile*' → 0 hits

### Risk Description

Cloud-Deployments improvisieren; reproduzierbares Build fehlt.

### Remediation

```
Multi-stage Dockerfile: builder (uv pip install) → runtime (slim, USER 1000, ENTRYPOINT ["lobbywatch-mcp"]).
```

### Effort Estimate

M (1-3d)
