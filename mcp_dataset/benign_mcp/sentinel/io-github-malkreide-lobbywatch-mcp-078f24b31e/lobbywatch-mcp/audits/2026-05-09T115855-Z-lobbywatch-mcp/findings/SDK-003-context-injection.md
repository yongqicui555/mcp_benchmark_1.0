## Finding: SDK-003 — Context Injection für Progress Reports und Logging

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SDK-003

### Observed Behavior

Kein ctx: Context Parameter; refresh_dump (Long-running, ~17 MB Download) hat keine Progress-Reports.

### Expected Behavior

Best-Practice-Katalog (SDK-003). Siehe checks/SDK-003.md für volle Pass-Criteria.

### Evidence

grep Context|ctx: src/lobbywatch_mcp/server.py → 0 hits

### Risk Description

User wartet blind während Dump-Download (10–60 s); kein progress-Feedback ans LLM.

### Remediation

```
async def refresh_dump(ctx: Context) -> ...:
    await ctx.info('Downloading weekly dump...')
    await ctx.report_progress(0.5, 1.0, 'Downloading...')
```

### Effort Estimate

S (< 1d)
