## Finding: SEC-019 — Lethal Trifecta: Bewertung dokumentieren

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `SEC-019` |
| **PDF-Reference** | Sec 4.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Server has at most ONE leg of the lethal trifecta: it reads only PUBLIC data (no private data), has no write/send/exfiltration channel, and returns results only to the calling LLM
- Receiver allow-list present as a frozenset (ALLOWED_HOSTS, server.py:45)

### Gaps vs. Pass Criteria

- No explicit lethal-trifecta assessment / ADR in docs/security.md (the threat model exists but does not state the trifecta evaluation) — remediation is a short documentation addition; the server does NOT possess the trifecta

### Expected Behavior

An explicit lethal-trifecta assessment in docs/ confirming the server holds at most two of {private-data access, untrusted-content exposure, exfiltration}; receiver allow-lists as frozensets.

### Risk Description

The server does NOT possess the trifecta (public data only, no send/write channel), but the absence of a written assessment means a future contributor could add an exfiltration-capable tool without re-evaluating.

### Remediation

Add a short 'Lethal Trifecta' subsection to docs/security.md stating: data is public (not private), no outbound send/write capability, egress restricted to ALLOWED_HOSTS — therefore the trifecta is not present. Re-evaluate on any new tool with a send/write side effect.

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `SEC-019` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.
