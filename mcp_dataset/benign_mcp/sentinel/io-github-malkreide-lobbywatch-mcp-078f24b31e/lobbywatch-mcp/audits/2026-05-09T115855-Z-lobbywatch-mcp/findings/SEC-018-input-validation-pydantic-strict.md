## Finding: SEC-018 — Input-Validation an Tool-Boundaries (Pydantic strict)

**Severity:** high
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SEC-018

### Observed Behavior

Pydantic-Modelle nutzen extra='allow' und kein strict-Mode. Tool-Parameter haben unbegrenzte Range.

### Expected Behavior

Best-Practice-Katalog (SEC-018). Siehe checks/SEC-018.md für volle Pass-Criteria.

### Evidence

src/lobbywatch_mcp/models.py:19,28,51,67,81 ConfigDict(extra='allow')
src/lobbywatch_mcp/server.py:202 limit: int = 25 (kein Upper Bound)
server.py:223 branche_query.strip().lower() (kein Length-Check)

### Risk Description

DoS via `limit=10**9` triggert Full-Scan über alle 245 Parlamentarier × 7800 IBs. Unbegrenzte Strings können RegEx-Engines stressen.

### Remediation

```
Annotated[int, Field(ge=1, le=200)] für limit; Annotated[str, Field(min_length=1, max_length=200)] für query-Strings; ConfigDict(extra='forbid') für Response-Modelle.
```

### Effort Estimate

M (1-3d)
