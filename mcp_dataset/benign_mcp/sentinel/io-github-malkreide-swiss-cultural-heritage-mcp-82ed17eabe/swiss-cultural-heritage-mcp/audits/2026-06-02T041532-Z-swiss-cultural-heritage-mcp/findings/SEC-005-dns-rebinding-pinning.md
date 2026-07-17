## Finding: SEC-005 — DNS-Rebinding-Prevention: DNS-Pinning

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `SEC-005` |
| **PDF-Reference** | Sec 4.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Only two fixed Swiss-federal hosts are reachable (ALLOWED_HOSTS), so a rebinding attack would require compromising DNS for ckan.opendata.swiss or helveticat.nb.admin.ch

### Gaps vs. Pass Criteria

- No DNS pinning: httpx resolves per request, so a strict reading leaves a theoretical TOCTOU window (low real risk given the closed allow-list)

### Expected Behavior

DNS resolved once per request and the resolved IP pinned for the TCP connection; original hostname kept for SNI/Host/cert validation.

### Risk Description

Theoretical TOCTOU only: an attacker would need to control DNS for one of the two fixed Swiss-federal hosts. Real-world risk is minimal given the closed allow-list.

### Remediation

If hardening to spec: use a custom httpx transport/resolver that pins the first resolved A/AAAA record and validates the certificate against the original hostname. Treat as low priority while the allow-list holds two trusted hosts.

### Effort Estimate

**M**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `SEC-005` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.
