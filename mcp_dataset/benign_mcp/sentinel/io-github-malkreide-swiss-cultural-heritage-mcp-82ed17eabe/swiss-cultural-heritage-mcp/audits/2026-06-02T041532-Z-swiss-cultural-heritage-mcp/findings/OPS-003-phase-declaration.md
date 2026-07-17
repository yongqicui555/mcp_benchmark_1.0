## Finding: OPS-003 — Phasenarchitektur: Phase explizit deklarieren

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `OPS-003` |
| **PDF-Reference** | App. C |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Server is consistently Phase 1 (read-only): all tools readOnlyHint:true, no destructive/write tools — annotations match the phase
- CHANGELOG 0.1.0 references 'Phase 1 implementation'

### Gaps vs. Pass Criteria

- Current phase is not explicitly declared in README
- No roadmap file with phase-specific tasks / transition prerequisites

### Expected Behavior

Current phase (1/2/3) declared in README; a roadmap file with phase-specific tasks and documented transition prerequisites.

### Risk Description

Without an explicit phase declaration, contributors may add write/destructive tools without triggering the Phase 1->2 gate (audit, ISDS, DSG processing record).

### Remediation

Add a 'Phase' line to the README ('Phase 1 — read-only') and a `docs/roadmap.md` listing Phase 1 scope and the Phase 2 prerequisites. Record phase transitions in CHANGELOG.

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `OPS-003` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.
