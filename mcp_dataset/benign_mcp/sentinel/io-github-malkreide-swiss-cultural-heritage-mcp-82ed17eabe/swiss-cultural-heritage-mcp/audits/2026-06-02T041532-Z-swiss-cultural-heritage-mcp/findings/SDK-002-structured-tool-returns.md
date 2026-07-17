## Finding: SDK-002 — Strukturierte Tool-Returns / Response-Envelope

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `SDK-002` |
| **PDF-Reference** | Sec 3.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Pydantic >=2 in dependencies; all *Input classes are typed Pydantic v2 models with Field defaults and a ResponseFormat StrEnum (server.py:93)

### Gaps vs. Pass Criteria

- All tools are annotated -> str and return formatted markdown / json-as-string, not structured Pydantic/TypedDict objects
- No consistent response envelope (source/provenance/results/count) on search/list tools

### Expected Behavior

Tools return typed objects (Pydantic/TypedDict/dict[str,X]) with a consistent envelope (source, provenance, results, count), not hand-built strings.

### Risk Description

String returns force the client to re-parse markdown; there is no machine-stable contract, so downstream automation is fragile and counts/provenance are inconsistent.

### Remediation

Define a `SearchResult`/`ResultEnvelope` Pydantic model (`source`, `count`, `results`, optional `has_more`) and return it from search/list tools; keep a `response_format='markdown'` rendering as a thin view over the structured object.

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `SDK-002` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.
