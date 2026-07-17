## Finding: ARCH-003 — «Not Found» Anti-Pattern: Heuristiken statt leerer Antworten

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `ARCH-003` |
| **PDF-Reference** | Sec 2.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Empty-result paths return actionable hints, not bare empties (heritage_browse_collection tip to check resource IDs server.py:646; helveticat tip server.py:783)

### Gaps vs. Pass Criteria

- No match_type field (exact/fuzzy/none) in responses
- No fuzzy-match or suggestion mechanism on zero hits

### Expected Behavior

Search tools that return no results should offer a fuzzy match or a suggestion mechanism and expose a match_type field (exact/fuzzy/none); on none, give an actionable hint.

### Risk Description

On a typo or near-miss query the LLM gets a flat «keine Treffer» and tends to give up or hallucinate, instead of being steered to a corrected term or a sibling tool.

### Remediation

Add a `match_type` field to JSON responses; on zero exact hits for SIKART/SNM, retry with a loosened CKAN `q` (partial/OR) and label results `fuzzy`. Keep the existing textual tips. OAI-PMH (NB) has no server-side search, so document the exact-only behaviour there.

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `ARCH-003` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.
