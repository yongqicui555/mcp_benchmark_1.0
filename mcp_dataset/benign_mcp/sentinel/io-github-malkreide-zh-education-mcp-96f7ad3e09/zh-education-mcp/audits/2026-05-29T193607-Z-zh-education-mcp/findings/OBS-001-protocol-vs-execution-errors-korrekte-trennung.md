## Finding: OBS-001 — Protocol vs. Execution Errors: korrekte Trennung

**Severity:** high
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** OBS-001
**PDF-Reference:** Sec 6.1

### Observed Behavior / Evidence
- Tool-Handler fangen Exceptions ab und geben handlungsorientierte Strings zurück statt zu raisen (server.py:76-89,322-323)
- HTTP-Statuscode-spezifische Meldungen (404/429/502/503)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Fehler werden als normaler String zurückgegeben, nicht als isError:true tool-result
- Keine standardisierten JSON-RPC-Fehlercodes (-326xx/-320xx)
- Kein dedizierter Test für Protocol-Error-Pfad

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)
