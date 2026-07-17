# Finding: SEC-008 — Keine explizite First-Run-Approval (Restrisiko, niedrig)

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | accepted-risk |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `SEC-008` |
| **Audit-Datum** | 2026-05-09 |

### Observed Behavior

Standard-Installation via `uvx bakom-mcp` und `claude_desktop_config.json`. Keine post-install-Scripts. Keine First-Run-Approval-Logik im Code.

### Expected Behavior

Pre-Configuration Consent: User wird vor erstem Tool-Call explizit informiert, welche externen APIs angesprochen werden, dass keine Auth erfolgt, und welche Datenkategorien zurückkommen.

### Evidence

- `grep "consent|first.run|approve" src/`: 0 Treffer
- README.md erklärt das implizit ("Open Government Data, no auth")

### Risk Description

- Gering: Server ist read-only auf Public OGD, keine PII, keine Schreib-Operation
- User-Konsens kommt ohnehin implizit über die Claude-Desktop-Tool-Approval-UI

### Remediation

**Optional** — README-Sektion «What this server does and does not» konkretisieren. Z.B.:

```markdown
## What this server does

✓ Reads BAKOM open data via three public APIs:
  - api3.geo.admin.ch (broadband / mobile coverage)
  - ckan.opendata.swiss (telecom statistics)
  - rtvdb.ofcomnet.ch (RTV database)

## What it does not

✗ Send data anywhere (read-only)
✗ Access local filesystem
✗ Use authentication tokens (none required)
✗ Cache or persist user inputs
```

Plus: First-Tool-Call kann optional einen Hinweis-Banner ausgeben (eher Anti-Pattern, daher nur Doku).

### Effort Estimate

**S** — Doku-Edit.

### Verification After Fix

README enthält «What this server does and does not»-Sektion.
