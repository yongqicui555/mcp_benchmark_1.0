## Finding: ARCH-008 — Drei Primitive nutzen: Tools, Resources und Prompts

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** ARCH-008

### Observed Behavior

Nur @mcp.tool verwendet; keine Resources oder Prompts.

### Expected Behavior

Best-Practice-Katalog (ARCH-008). Siehe checks/ARCH-008.md für volle Pass-Criteria.

### Evidence

grep -rn '@mcp\.(resource|prompt)' src/ → 0 hits

### Risk Description

Verfehlt MCP-Architektur-Mehrwert: Attribution-Text als Resource, Anchor-Demo-Query als Prompt würden LLM-Lifecycle besser bedienen.

### Remediation

```
@mcp.resource('lobbywatch://attribution') → liefert ATTRIBUTION-String
@mcp.prompt('wbk_education_conflicts') → kanonischer Demo-Prompt aus README
```

### Effort Estimate

M (1-3d)
