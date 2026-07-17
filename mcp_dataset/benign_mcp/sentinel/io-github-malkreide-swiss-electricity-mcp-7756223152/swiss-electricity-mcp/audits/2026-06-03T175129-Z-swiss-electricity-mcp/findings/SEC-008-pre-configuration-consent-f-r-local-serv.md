## Finding: SEC-008 — Pre-Configuration Consent für Local-Server-Installation

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `SEC-008` |
| **PDF-Reference** | Sec 4.5 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Keine pre/postinstall-Hooks (reines Python-Paket, hatchling); keine dynamischen Setup-Scripts
- README zeigt vollen Installationsbefehl transparent; CONTRIBUTING.md erklaert Build

### Gaps / Abweichung vom Pass-Kriterium

- Keine PyPI-OIDC-Trusted-Publisher/Sigstore-Signatur (kein publish-Workflow, .github fehlt)

### Risk Description

Wenn ein User einen lokalen MCP-Server installiert (typischerweise via `claude_desktop_config.json`), wird ein Subprozess mit User-Privilegien gestartet. Der Befehl steht in der Konfig-Datei — `npx -y @malkreide/zh-education-mcp`, `uvx zh-education-mcp`, etc.

### Remediation

### Schritt 1: Hooks entfernen

```diff
  {
    "scripts": {
-     "postinstall": "node ./scripts/setup.js",
      "build": "tsc",
      "start": "node dist/server.js"
    }
  }
```

Falls Setup wirklich nötig ist: als separater, dokumentierter Schritt nach Installation, nicht automatisch.

### Schritt 2: README-Transparenz

Vollen Befehl mit Erklärung wie im Pass-Pattern. Kein Hide-Behind-One-Liner.

### Schritt 3: PyPI-Trusted-Publisher konfigurieren

Auf pypi.org → Project Settings → Publishing → Add trusted publisher mit GitHub-Repo.

```yaml
# .github/workflows/release.yml
on:
  push:
    tags: ['v*']

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
      - run: pip install build && python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
        # Sigstore-Signaturen automatisch
```

### Schritt 4: User-seitige Empfehlung im README

```markdown

### Effort Estimate

S — < 1 Tag. Hauptaufwand: Trusted-Publisher-Setup auf PyPI/npm + README-Update.

### Verification After Fix

- Re-Audit von `SEC-008` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)
