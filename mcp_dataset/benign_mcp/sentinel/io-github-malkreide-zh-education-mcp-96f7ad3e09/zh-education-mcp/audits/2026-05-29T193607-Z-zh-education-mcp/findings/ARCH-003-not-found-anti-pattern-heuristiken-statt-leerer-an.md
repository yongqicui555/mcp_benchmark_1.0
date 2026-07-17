## Finding: ARCH-003 — «Not Found» Anti-Pattern: Heuristiken statt leerer Antworten

**Severity:** medium
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** ARCH-003
**PDF-Reference:** Sec 2.2

### Observed Behavior / Evidence
- zh_edu_schulkreis_trend liefert Fuzzy-Vorschläge + Hinweis bei Not-Found (server.py:359-366)
- Mehrere Tools verweisen bei Not-Found auf zh_edu_list_schulgemeinden (server.py:516-519,585-589)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein match_type-Feld (exact/fuzzy/none) in den Antworten
- Fuzzy-Fallback nur in einem Tool; sek1_profil/staatsangehoerigkeiten geben Hinweis ohne Vorschläge

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)
