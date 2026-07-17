## Finding: ARCH-008 — Drei MCP-Primitive nutzen

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** ARCH-008
**Verification-Status:** partial

### Observed Behavior / Evidence
- Server nutzt ausschliesslich das Tools-Primitiv (6 Tools), keine Resources/Prompts

### Gaps vs. Best-Practice
- Keine dokumentierte Begründung im README, warum nur Tools verwendet werden (Pass-Kriterium); read-only get_*-Tools sind Resource-Kandidaten

### Remediation
Siehe Check `ARCH-008` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
M
