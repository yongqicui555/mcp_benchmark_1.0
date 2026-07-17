## Finding: SEC-004 — SSRF-Prevention: HTTPS-Enforce + IP-Blocklisting (Defense-in-Depth)

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `SEC-004` |
| **PDF-Reference** | Sec 4.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Host egress allow-list enforced before every request and re-checked on every redirect hop (server.py:112-139); a redirect to 169.254.169.254 would be rejected because it is not in ALLOWED_HOSTS
- All request hosts are built from module constants; no user input controls the host (only query/resource_id params)

### Gaps vs. Pass Criteria

- No explicit https-scheme assertion in _assert_allowed
- No resolved-IP blocklist (private/link-local/loopback/IPv6) and no DNS-pin against TOCTOU — the SSRF vector is closed in practice by the 2-host allow-list, so IP-level controls are defense-in-depth, not a live exposure

### Expected Behavior

Explicit https-scheme check before each request; resolved-IP blocklist for private/link-local/loopback incl. 169.254.169.254 and IPv6 (::1, fe80::/10); single DNS resolution reused (no TOCTOU).

### Risk Description

Low live risk: the 2-host egress allow-list already blocks metadata IPs and there is no user-controlled host. The gap is missing belt-and-suspenders IP-level controls should the allow-list ever widen or a host be added carelessly.

### Remediation

In _assert_allowed also assert `httpx.URL(url).scheme == 'https'`; optionally add a resolved-IP blocklist guard for defense-in-depth. Keep the host allow-list as the primary control. Prioritise below the code-finding backlog given the closed allow-list.

### Effort Estimate

**M**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `SEC-004` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.
