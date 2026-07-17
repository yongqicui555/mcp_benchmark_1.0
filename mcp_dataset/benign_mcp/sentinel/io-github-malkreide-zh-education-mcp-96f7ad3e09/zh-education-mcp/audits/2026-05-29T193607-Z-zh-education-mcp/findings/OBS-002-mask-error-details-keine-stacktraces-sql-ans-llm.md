## Finding: OBS-002 — Mask Error Details: keine Stacktraces / SQL ans LLM

**Severity:** high
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** OBS-002
**PDF-Reference:** Sec 6.2

### Observed Behavior / Evidence
- Keine traceback.format_exc()-Ausgaben in Tool-Returns
- Bekannte Fehlertypen liefern user-freundliche, sanitisierte Meldungen (server.py:78-86)

### Gaps (Abweichung vom Best-Practice-Katalog)
- FastMCP ohne mask_error_details=True initialisiert (server.py:29)
- Generischer Fallback leakt Exception-Detail an den LLM: f'...({type(e).__name__}): {e}' (server.py:89)
- Originalfehler landen nirgends in einem Server-Log (kein Logging vorhanden)

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)
