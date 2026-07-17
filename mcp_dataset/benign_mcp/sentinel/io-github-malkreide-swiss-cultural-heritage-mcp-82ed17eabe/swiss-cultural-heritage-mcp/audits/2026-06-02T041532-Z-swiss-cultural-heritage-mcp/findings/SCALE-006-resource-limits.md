## Finding: SCALE-006 — Resource-Limits per Container (Memory, CPU, FDs)

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `SCALE-006` |
| **PDF-Reference** | Sec 5.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- docs/security.md and network-egress.md document k8s securityContext and NetworkPolicy

### Gaps vs. Pass Criteria

- No explicit memory/CPU resource limits or requests documented; no FD-limit/OOM guidance for the container

### Expected Behavior

Explicit memory and CPU limits (requests < limits), FD limit >= 4096 for many outbound connections, and tested clean OOM/restart behaviour.

### Risk Description

Without limits a runaway request (e.g. large OAI-PMH ListRecords parse) can exhaust the host; without a restart policy a crash means downtime.

### Remediation

Document recommended `resources.requests/limits` (e.g. 128Mi/256Mi, 100m/500m) in docs/, set `restartPolicy`, and note `ulimit -n` guidance. For Render, document the chosen instance size.

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `SCALE-006` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.
