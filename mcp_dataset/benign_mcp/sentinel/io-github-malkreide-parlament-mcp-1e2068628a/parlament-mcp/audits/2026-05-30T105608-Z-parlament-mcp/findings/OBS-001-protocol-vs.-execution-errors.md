## Finding: OBS-001 — Protocol vs. Execution Errors

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** OBS-001
**Verification-Status:** partial

### Observed Behavior / Evidence
- Tools fangen Exceptions via _handle_error() und liefern handlungsorientierte Fehlertexte statt JSON-RPC-Errors (server.py:102-115, 356-357)
- Empty-Results werden als normaler Text zurückgegeben, nicht als Error

### Gaps vs. Best-Practice
- Fehler werden als plain str zurückgegeben, nicht mit isError:true-Konvention
- Keine standardisierten JSON-RPC-Fehlercodes (-326xx)
- Kein Test deckt den Execution-Error-Pfad ab (kein Test mockt eine Exception)

### Remediation
Siehe Check `OBS-001` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
M
