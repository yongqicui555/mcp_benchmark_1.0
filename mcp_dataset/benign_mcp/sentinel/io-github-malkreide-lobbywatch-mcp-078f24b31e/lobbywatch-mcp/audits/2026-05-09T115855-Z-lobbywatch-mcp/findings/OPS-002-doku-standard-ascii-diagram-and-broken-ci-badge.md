## Finding: OPS-002 — Doku-Standard: bilingualer README, ASCII-Diagramm, Limits-Sektion

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** OPS-002

### Observed Behavior

Bilingual + Limits ✅, aber: ASCII-Architekturdiagramm fehlt; CI-Badge zeigt auf nicht-existenten Workflow.

### Expected Behavior

Best-Practice-Katalog (OPS-002). Siehe checks/OPS-002.md für volle Pass-Criteria.

### Evidence

README.md:3 [![CI](https://github.com/malkreide/lobbywatch-mcp/actions/workflows/ci.yml/badge.svg)] aber .github/workflows/ existiert nicht
Kein Diagramm dump-first / API-fallback

### Risk Description

Vertrauensverlust durch broken Badge (404). Architektur-Verständnis erschwert.

### Remediation

```
(a) ASCII-Diagramm: LLM → FastMCP → LobbywatchClient → {Dump-Cache | dataIF-Live} → cms.lobbywatch.ch
(b) .github/workflows/ci.yml anlegen ODER Badge entfernen.
```

### Effort Estimate

S (< 1d)
