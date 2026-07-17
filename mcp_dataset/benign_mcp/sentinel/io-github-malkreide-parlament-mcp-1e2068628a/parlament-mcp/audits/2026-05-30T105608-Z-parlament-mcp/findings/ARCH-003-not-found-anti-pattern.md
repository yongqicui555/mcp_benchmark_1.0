## Finding: ARCH-003 — «Not Found» Anti-Pattern

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** ARCH-003
**Verification-Status:** partial

### Observed Behavior / Evidence
- Tools liefern handlungsorientierte deutsche Not-Found-Texte statt leerer Listen (z.B. 'Keine Vorstösse gefunden…', server.py:360)

### Gaps vs. Best-Practice
- Kein match_type-Feld (exact/fuzzy/none) und kein Fuzzy-/Vorschlags-Mechanismus bei leeren Treffern

### Remediation
Siehe Check `ARCH-003` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S
