## Finding: SCALE-006 — Resource-Limits per Container (Memory, CPU, FDs)

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SCALE-006

### Observed Behavior

Keine Resource-Limits-Spec.

### Expected Behavior

Best-Practice-Katalog (SCALE-006). Siehe checks/SCALE-006.md für volle Pass-Criteria.

### Evidence

Kein Dockerfile / k8s-Manifest mit limits

### Risk Description

Dump (~17 MB komprimiert, ~80 MB im RAM) + 245 Records: ohne Memory-Limit kann ein Memory-Leak den Host instabil machen.

### Remediation

```
k8s-Manifest mit resources: requests {memory: 256Mi, cpu: 100m}, limits {memory: 512Mi, cpu: 500m}; ulimit -n im Dockerfile.
```

### Effort Estimate

S (< 1d)
