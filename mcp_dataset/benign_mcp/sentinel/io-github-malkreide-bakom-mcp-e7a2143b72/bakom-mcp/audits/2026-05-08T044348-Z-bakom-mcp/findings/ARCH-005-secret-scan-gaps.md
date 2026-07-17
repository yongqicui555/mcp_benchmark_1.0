# Finding: ARCH-005 — Secret-Scan-Gaps in Repo-Hygiene

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `ARCH-005` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

Im aktuellen Code sind **keine Hardcoded Secrets** vorhanden — der Server benötigt schliesslich keine (auth_model=none, alle Datenquellen sind OGD ohne Auth). Die Risiko-Lage entsteht aber durch fehlende präventive Hygiene-Massnahmen für künftige Contributions.

### Expected Behavior

- `.gitignore` enthält `.env`, `.env.local`, `*.secrets`, `credentials*`
- `.env.example` mit Platzhaltern (Doku-Hinweis)
- CI-Workflow mit Gitleaks oder Trufflehog auf jedem PR

### Evidence

- File: `.gitignore` — kein Eintrag für `.env`/`secrets`/`credentials`
- File: `.github/workflows/ci.yml` — kein Secret-Scan-Step
- Kein `.env.example` im Repo

### Risk Description

Falls ein Contributor künftig einen API-Key (z.B. für rate-limited Premium-API von ofcomnet) hinzufügt und versehentlich `.env` committet, gibt es keine Sicherheitsnetz: kein CI-Scan, kein lokaler Pre-Commit-Hook. Public Repo + Push = sofortiger Leak.

### Remediation

```bash
# .gitignore ergaenzen:
echo "
# Secrets
.env
.env.*
!.env.example
*.secrets
credentials.json" >> .gitignore

# .env.example anlegen:
cat > .env.example <<'EOF'
# bakom-mcp benoetigt aktuell keine Secrets.
# Diese Datei ist Platzhalter fuer kuenftige optionale Konfiguration.
# Beispiel:
# OPENDATA_SWISS_API_KEY=your-key-if-rate-limited
EOF
```

CI-Workflow:

```yaml
# .github/workflows/secret-scan.yml
name: Secret Scan
on: [push, pull_request]
jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with: { fetch-depth: 0 }
      - uses: gitleaks/gitleaks-action@v2
```

### Effort Estimate

**S** — < 1 Stunde.

### Verification After Fix

Re-grep nach Secret-Patterns + CI-Run zeigt Gitleaks-Step.
