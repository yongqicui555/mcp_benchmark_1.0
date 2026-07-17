## Finding: SDK-002 — Pydantic v2 / TypedDict / Dataclass als Tool-Returns

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SDK-002

### Observed Behavior

Tools returnen dict[str, Any] (nach .model_dump()) statt Pydantic-Modell direkt.

### Expected Behavior

Best-Practice-Katalog (SDK-002). Siehe checks/SDK-002.md für volle Pass-Criteria.

### Evidence

src/lobbywatch_mcp/server.py:147 -> dict[str, Any] (return ParlamentarierResponse(...).model_dump())

### Risk Description

FastMCP verliert Schema-Treue im Tool-Descriptor; Clients sehen generic 'object' statt strukturiertem Schema.

### Remediation

```
Direct return: -> ParlamentarierResponse mit return ParlamentarierResponse(...) (ohne .model_dump()).
```

### Effort Estimate

S (< 1d)
