## Finding: ARCH-012 — protocolVersion-Pinning + CHANGELOG

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** ARCH-012
**Verification-Status:** partial

### Observed Behavior / Evidence
- CHANGELOG.md im Keep-a-Changelog-Format mit SemVer-Bekenntnis (CHANGELOG.md:1-6)

### Gaps vs. Best-Practice
- protocolVersion nicht explizit gepinnt (grep protocol_version → nicht vorhanden) — nimmt SDK-Default
- Keine README-Sektion 'MCP Protocol Version' / Update-Policy
- Kein Dependabot/Renovate für monatliche SDK-Update-PRs

### Remediation
Siehe Check `ARCH-012` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S
