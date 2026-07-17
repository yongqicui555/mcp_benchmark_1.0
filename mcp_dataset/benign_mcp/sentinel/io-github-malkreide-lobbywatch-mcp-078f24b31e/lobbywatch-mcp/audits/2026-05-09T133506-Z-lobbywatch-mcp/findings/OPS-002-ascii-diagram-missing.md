## Finding: OPS-002 — Doku-Standard: ASCII-Architekturdiagramm

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** OPS-002

### Observed Behavior

`README.md` und `README.de.md` sind bilingual ✅, '## Known Limitations'-Sektion vorhanden ✅, CI-Badge zeigt nicht mehr auf einen 404 ✅ (`.github/workflows/ci.yml` existiert seit PR #2).

Was nach wie vor fehlt: ein knappes ASCII-Architekturdiagramm im README, das den dump-first / dataIF-fallback-Datenfluss visualisiert. Das vereinfacht den schnellen Architektur-Überblick für neue Contributors und Auditoren.

### Expected Behavior

Im README zwischen 'Overview' und 'Tools' ein 5-10 Zeilen langes Diagramm:

```
LLM ──► FastMCP ──► LobbywatchClient
                       │
                       ├──► Dump-Cache  ──► cms.lobbywatch.ch (weekly export)
                       │
                       └──► dataIF       ──► cms.lobbywatch.ch/de/data/interface
```

### Evidence

- `grep "Diagram\|architecture\|Architektur\|ASCII" README.md README.de.md` → 1 Treffer im README (nicht-Diagramm-Kontext)
- README zeigt 'Project Structure' als Filesystem-Tree, aber keinen Datenfluss

### Risk Description

Niedrig — rein kosmetisch. Kein Sicherheits- oder Korrektheitsrisiko. Nur Onboarding-Friction.

### Remediation

Direkt in `README.md` (und `README.de.md`) zwischen 'Features' und 'Prerequisites' einfügen:

```
## Architecture

LLM ──► FastMCP ──► LobbywatchClient
                       │
                       ├──► Dump cache  ──► cms.lobbywatch.ch (weekly export)
                       └──► dataIF      ──► cms.lobbywatch.ch/de/data/interface
```

### Effort Estimate

S (< 1d, ~10 Min)
