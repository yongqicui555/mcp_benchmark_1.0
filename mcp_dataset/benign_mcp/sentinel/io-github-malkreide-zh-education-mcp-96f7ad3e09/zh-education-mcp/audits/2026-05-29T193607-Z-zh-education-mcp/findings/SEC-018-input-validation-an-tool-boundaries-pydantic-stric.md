## Finding: SEC-018 — Input-Validation an Tool-Boundaries (Pydantic strict / Zod)

**Severity:** high
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** SEC-018
**PDF-Reference:** Sec 3 / Sec 4 (Defense-in-Depth)

### Observed Behavior / Evidence
- Alle Tool-Argumente über Pydantic-Modelle validiert (server.py:133-268)
- Numerische Felder mit ge/le (letzte_n_jahre ge=1 le=30; top_n ge=1 le=100)
- String-Felder mit min_length/max_length; ConfigDict(extra='forbid') konsequent gesetzt

### Gaps (Abweichung vom Best-Practice-Katalog)
- strict=True nicht gesetzt ⇒ Type-Coercion möglich
- Keine Whitelist-pattern auf String-Feldern
- Keine Edge-Case-Tests (zu lange Strings, Out-of-Range, unbekannte Felder)

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)
