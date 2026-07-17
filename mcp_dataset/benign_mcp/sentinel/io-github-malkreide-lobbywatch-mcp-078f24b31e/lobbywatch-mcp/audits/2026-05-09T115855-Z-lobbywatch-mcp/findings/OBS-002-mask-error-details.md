## Finding: OBS-002 — Mask Error Details: keine Stacktraces / SQL ans LLM

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** OBS-002

### Observed Behavior

Error-Strings enthalten interne Strukturen (zip-Member-Listing, Type-Names).

### Expected Behavior

Best-Practice-Katalog (OBS-002). Siehe checks/OBS-002.md für volle Pass-Criteria.

### Evidence

src/lobbywatch_mcp/client.py:140 RuntimeError(f'Dump does not contain expected file. Got: {zf.namelist()}')
client.py:150 f'Unexpected dump shape: {type(data).__name__}'

### Risk Description

Interne Pfad-/Schema-Details propagieren ins LLM-Context und können als Reconnaissance-Hilfe dienen.

### Remediation

```
Generische User-Facing-Message + Detailed-Internal-Log: 
logger.error('Dump shape mismatch: %s', zf.namelist())
raise RuntimeError('Lobbywatch dump format unexpected; refresh required.')
```

### Effort Estimate

S (< 1d)
