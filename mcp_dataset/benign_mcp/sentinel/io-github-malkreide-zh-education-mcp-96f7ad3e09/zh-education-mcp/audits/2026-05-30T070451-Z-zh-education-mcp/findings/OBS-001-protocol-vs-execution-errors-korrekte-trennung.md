## Finding: OBS-001 — Protocol vs. Execution Errors: korrekte Trennung

**Severity:** high
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** OBS-001
**PDF-Reference:** Sec 6.1

### Observed Behavior / Evidence
- Tool-Handler fangen Exceptions ab, geben handlungsorientierte Antworten (data._handle_error)
- Format-bewusste Not-Found-Antworten

### Gaps (Abweichung vom Best-Practice-Katalog)
- Fehler weiterhin als String/Envelope statt isError:true tool-result (bewusster UX-Entscheid, dokumentiert)
- Keine standardisierten JSON-RPC-Fehlercodes

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)
