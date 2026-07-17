## Finding: SEC-022 — Tool-Hash-Pinning + Namespace-Präfix gegen Rug Pull

**Severity:** high
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** SEC-022
**PDF-Reference:** Anhang B4

### Observed Behavior / Evidence
- Konsistentes Namespace-Präfix zh_edu_ über alle Tools (server.py)
- CHANGELOG nennt Tools beim Namen; SemVer im CHANGELOG-Header erklärt

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein Hash-Snapshot der Tool-Definitionen bei Releases (Rug-Pull-Detection)
- Präfix nutzt zh_edu_ statt des empfohlenen <server>__<tool>-Schemas
- Keine User-Re-Approval-Hinweise bei Tool-Description-Änderungen

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)
