## Finding: SEC-007 — Container-Sandboxing: Docker / chroot mit minimalen Privilegien

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SEC-007

### Observed Behavior

Kein Dockerfile vorhanden; keine seccomp/AppArmor-Profile.

### Expected Behavior

Best-Practice-Katalog (SEC-007). Siehe checks/SEC-007.md für volle Pass-Criteria.

### Evidence

find . -name 'Dockerfile*' -o -name 'docker-compose*' → 0 hits

### Risk Description

Cloud-Deployment ohne Container = Process auf Host mit voller Privilege-Surface.

### Remediation

```
Multi-stage Dockerfile (siehe SCALE-004) mit `USER 1000`, `--read-only` rootfs, drop ALL capabilities ausser NET_BIND_SERVICE.
```

### Effort Estimate

M (1-3d)
