## Finding: SDK-002 — Strukturierte Tool-Returns

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SDK-002
**Verification-Status:** partial

### Observed Behavior / Evidence
- Pydantic v2 als Dependency (pyproject.toml:32) und für alle Tool-INPUTS genutzt

### Gaps vs. Best-Practice
- Alle Tools haben Rückgabetyp '-> str' (Markdown/JSON-String) statt strukturierter BaseModel/TypedDict-Returns
- Kein konsistenter Response-Envelope mit source/provenance/count → FastMCP exponiert kein Output-Schema

### Remediation
Siehe Check `SDK-002` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S
