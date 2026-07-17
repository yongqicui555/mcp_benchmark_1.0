## Finding: SDK-003 — Context Injection für Progress Reports und Logging

**Severity:** medium
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** SDK-003
**PDF-Reference:** Sec 3.1

### Observed Behavior / Evidence
- Operationen sind durch 24h-Cache meist schnell (server.py:53-66)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein Tool nutzt ctx: Context; keine ctx.report_progress() bei potenziell langem Cold-Fetch (Timeout 30s, server.py:33)
- Kein ctx.info()/ctx.warning()-Logging

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)
