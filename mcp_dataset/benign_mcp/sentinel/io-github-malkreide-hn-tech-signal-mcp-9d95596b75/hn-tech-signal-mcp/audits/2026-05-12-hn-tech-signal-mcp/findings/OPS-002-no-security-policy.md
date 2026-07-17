# Finding: OPS-002 — Kein SECURITY.md, kein Dependabot, kein CODEOWNERS

| Feld | Wert |
|---|---|
| **Severity** | **low** |
| **Status** | closed (re-audit 2026-05-12) |
| **Server** | `hn-tech-signal-mcp` |
| **Check-Reference** | `OPS-003` (Supply-Chain Posture) |
| **Audit-Datum** | 2026-05-12 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

`ls .github/` zeigt nur `workflows/`. Es fehlen:
- `SECURITY.md` (Vulnerability-Reporting-Pfad)
- `.github/dependabot.yml` (automatische Dependency-Updates)
- `CODEOWNERS` (Review-Routing)
- Issue-/PR-Templates

### Expected Behavior

Open-Source-MCP-Server, der PyPI-publiziert (`pypi.org/project/hn-tech-signal-mcp/`) ist, sollte:
1. Sicherheits-Kontaktpfad via `SECURITY.md` exponieren.
2. Dependabot `pip`/`github-actions` aktiviert haben.
3. Mindestens einen CODEOWNER für `src/` definieren.

### Evidence

- `find .github -type f` → nur `workflows/ci.yml`, `workflows/publish.yml`
- `find . -maxdepth 2 -iname "SECURITY*"` → keine Treffer

### Risk Description

- Vulnerability-Finder hat keinen klaren Reporting-Pfad — landet öffentlich im Issue-Tracker.
- Bekannte CVEs in `httpx`/`pydantic`/`mcp` werden nicht automatisch erkannt.

### Remediation

1. `SECURITY.md` mit Reporting-E-Mail oder GitHub-Security-Advisory-Link.
2. `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule: { interval: "weekly" }
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule: { interval: "monthly" }
```

3. `CODEOWNERS` mit `* @malkreide`.

### Effort Estimate

**S** — < 1 Stunde.

### Verification After Fix

- GitHub-Insights/Security-Tab zeigt aktivierten Dependabot
- PR auf `src/` notifiziert CODEOWNER automatisch
