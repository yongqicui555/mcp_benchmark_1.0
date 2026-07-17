## Finding: SEC-005 — DNS-Rebinding-Prevention: DNS-Pinning gegen TOCTOU

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SEC-005

### Observed Behavior

Kein DNS-Pinning. httpx-Default verwendet OS-Resolver pro Request.

### Expected Behavior

Best-Practice-Katalog (SEC-005). Siehe checks/SEC-005.md für volle Pass-Criteria.

### Evidence

grep DNS|resolve|getaddrinfo src/ → 0 hits

### Risk Description

Bei HTTP-Transport mit 0.0.0.0-Binding (siehe SEC-016): malicious DNS-Antwort kann zwischen TOCTOU-Window auf Metadata-IP wechseln.

### Remediation

```
Custom httpx Transport mit IP-pinning beim Startup, oder pinning der `cms.lobbywatch.ch`-Auflösung mit TTL-Cache.
```

### Effort Estimate

M (1-3d)
