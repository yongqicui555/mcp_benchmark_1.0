## Finding: SDK-002 — Strukturierte Tool-Returns

**Severity:** medium
**Status:** accepted-risk (dokumentiert)
**Server:** parlament-mcp
**Verification-Status:** partial

### Observed Behavior / Evidence
- Pydantic v2 für Inputs; konsistenter JSON-Envelope mit source/license/provenance/match_type/count

### Gaps vs. Best-Practice
- Tool-Returns bleiben bewusst str (Markdown-Default für Lesbarkeit) statt BaseModel — explizite, dokumentierte Backward-Compat-Entscheidung; volle strukturierte Returns erst bei Bedarf

### Remediation
Bewusst zurückgestellt — siehe docs/roadmap.md (Phase 3) bzw. ADR. Kein
Blocker für die aktuelle read-only/no-auth Phase-1-Anbindung.

### Effort Estimate
M (an Auth/Phase-3 gekoppelt)
