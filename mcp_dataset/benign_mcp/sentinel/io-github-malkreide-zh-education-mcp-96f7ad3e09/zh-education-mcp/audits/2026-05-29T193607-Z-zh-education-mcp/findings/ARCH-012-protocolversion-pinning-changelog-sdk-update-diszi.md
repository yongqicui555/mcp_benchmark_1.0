## Finding: ARCH-012 — protocolVersion-Pinning + CHANGELOG + SDK-Update-Disziplin

**Severity:** medium
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** ARCH-012
**PDF-Reference:** Anhang A9

### Observed Behavior / Evidence
- CHANGELOG.md im Keep-a-Changelog-Format vorhanden (CHANGELOG.md)

### Gaps (Abweichung vom Best-Practice-Katalog)
- protocolVersion nirgends explizit gepinnt (grep: keine Treffer)
- Keine README-Sektion 'MCP Protocol Version' und keine Update-Policy
- Kein Dependabot/Renovate für SDK-Updates
- CHANGELOG nennt keine Spec-Version-Bumps

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)
