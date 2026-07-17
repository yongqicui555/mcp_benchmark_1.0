## Finding: ARCH-012 — protocolVersion-Pinning + SDK-Update-Disziplin

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `ARCH-012` |
| **PDF-Reference** | Sec 2.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- CHANGELOG.md present and in Keep-a-Changelog format with SemVer

### Gaps vs. Pass Criteria

- protocolVersion is NOT explicitly pinned in server code (relies on SDK default)
- No 'MCP Protocol Version' section in README
- No Dependabot/Renovate config for monthly SDK update PRs

### Expected Behavior

protocolVersion explicitly pinned in code; a README 'MCP Protocol Version' section with an update policy; Dependabot/Renovate for monthly SDK PRs.

### Risk Description

An SDK upgrade can silently bump the negotiated protocol version; without pinning and a changelog discipline, behaviour drifts between releases unnoticed.

### Remediation

Document and (where the SDK exposes it) pin the supported MCP protocol version; add a 'MCP Protocol Version' README section; add `.github/dependabot.yml` (pip, weekly/monthly) so `mcp` upgrades arrive as reviewable PRs.

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `ARCH-012` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.
