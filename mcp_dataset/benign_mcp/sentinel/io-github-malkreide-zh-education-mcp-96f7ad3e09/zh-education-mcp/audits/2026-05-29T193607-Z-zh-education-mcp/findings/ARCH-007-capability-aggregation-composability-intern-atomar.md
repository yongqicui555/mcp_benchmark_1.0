## Finding: ARCH-007 — Capability-Aggregation: Composability intern, Atomarität extern

**Severity:** medium
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** ARCH-007
**PDF-Reference:** Sec 2.3

### Observed Behavior / Evidence
- Tools liefern abgeschlossene Resultate (Markdown-Tabellen/JSON), keine reinen IDs
- Aggregation pro Tool aus einem Endpunkt, gecacht

### Gaps (Abweichung vom Best-Practice-Katalog)
- Keine Provenance/source-Info in den aggregierten Outputs (Synergie CH-004/SDK-002)
- Keine asyncio.gather-Parallelisierung (aber auch nur 1 Fetch pro Tool)

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)
