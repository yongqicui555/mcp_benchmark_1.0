## Finding: OBS-003 — Structured Logging mit RFC 5424 Severity-Stufen

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** OBS-003

### Observed Behavior

Python-Standard-Logging ohne JSON/structlog; keine Request-IDs.

### Expected Behavior

Best-Practice-Katalog (OBS-003). Siehe checks/OBS-003.md für volle Pass-Criteria.

### Evidence

Nur logging.getLogger(__name__) in src/

### Risk Description

Schwer in SIEM zu indizieren; keine Korrelation Tool-Call ↔ Log-Lines.

### Remediation

```
structlog mit JSONRenderer; pro Tool-Call eine UUID4-Correlation-ID via context.
```

### Effort Estimate

M (1-3d)
