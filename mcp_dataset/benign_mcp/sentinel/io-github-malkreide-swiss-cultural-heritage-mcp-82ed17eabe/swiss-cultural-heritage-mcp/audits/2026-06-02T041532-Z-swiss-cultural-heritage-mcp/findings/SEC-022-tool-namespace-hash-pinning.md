## Finding: SEC-022 — Tool-Hash-Pinning + Namespace-Präfix gegen Rug Pull

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `SEC-022` |
| **PDF-Reference** | Sec 4.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- All tools share a consistent heritage_ namespace prefix
- Breaking tool changes are tracked in CHANGELOG with SemVer major bumps (e.g. removal of period/technique params)

### Gaps vs. Pass Criteria

- Prefix is heritage_, not the server-identity form <server>__<tool>
- No tool-definition hash snapshot generated at release for rug-pull detection
- No explicit user re-approval note on description changes

### Expected Behavior

Tools namespaced with server identity (<server>__<tool>); a tool-definition hash snapshot generated per release; CHANGELOG flags tool-description changes with a re-approval note.

### Risk Description

A silently changed tool description (rug pull) could re-task the LLM. The heritage_ prefix is consistent but not server-identified, and there is no release-time hash to detect definition drift.

### Remediation

Optionally adopt a `<server>__<tool>` prefix (breaking — major bump); add a release step that hashes tool names+descriptions+schemas into `audits/tool-pins/<version>.json`; add a CHANGELOG note when any tool description changes, prompting user re-approval.

### Effort Estimate

**M**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `SEC-022` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.
