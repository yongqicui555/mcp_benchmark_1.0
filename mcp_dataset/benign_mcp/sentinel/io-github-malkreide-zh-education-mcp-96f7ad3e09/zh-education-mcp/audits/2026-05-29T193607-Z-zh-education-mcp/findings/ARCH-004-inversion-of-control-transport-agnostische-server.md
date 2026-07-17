## Finding: ARCH-004 — Inversion of Control: Transport-agnostische Server-Logik

**Severity:** high
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** ARCH-004
**PDF-Reference:** Sec 2.1

### Observed Behavior / Evidence
- Tool-Handler greifen nicht auf request zu; Logik ist transport-agnostisch
- stdio + streamable-http werden beide unterstützt (server.py:853-866)
- Identische Outputs unabhängig vom Transport

### Gaps (Abweichung vom Best-Practice-Katalog)
- Transport-Wahl über sys.argv-Parsing statt ENV-Var/Settings-Objekt (server.py:857-861)
- Konfiguration über globale Modul-Konstanten statt Pydantic-Settings (server.py:32-42)
- Kein ctx: Context in Handlern

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)
