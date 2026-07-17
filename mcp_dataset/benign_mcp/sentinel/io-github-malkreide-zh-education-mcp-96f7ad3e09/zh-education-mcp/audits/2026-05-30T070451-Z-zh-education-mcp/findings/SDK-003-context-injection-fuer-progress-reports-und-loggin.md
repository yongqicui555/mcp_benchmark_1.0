## Finding: SDK-003 — Context Injection für Progress Reports und Logging

**Severity:** medium
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** SDK-003
**PDF-Reference:** Sec 3.1

### Observed Behavior / Evidence
- Operationen durch 24h-Cache + gepoolten Client schnell

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein ctx: Context / ctx.report_progress() — Operationen sind kurz (Single-Fetch, gecacht); bewusst nicht nachgerüstet

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)
