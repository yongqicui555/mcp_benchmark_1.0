## Finding: OPS-002 — Doku-Standard: bilingualer README, ASCII-Diagramm, Limits-Sektion

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `OPS-002` |
| **PDF-Reference** | Anhang C2 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- README.md mit allen Kern-Sektionen (Anchor-Demo, Installation, Tools, Cloud, Architecture, Testing, Known limitations, Licensing)
- README.de.md parallel; CHANGELOG.md + CONTRIBUTING.md (bilingual) + EXAMPLES.md vorhanden

### Gaps / Abweichung vom Pass-Kriterium

- Architektur-Sektion ist narrativ - kein ASCII-/Mermaid-Architekturdiagramm

### Risk Description

ARCH-011 verlangt die Existenz von `README.md`, `README.de.md`, `CHANGELOG.md` als Files. OPS-002 verlangt **Inhalt-Disziplin** für diese Files — nicht nur Existenz.

### Remediation

### Schritt 1: README-Skelett

Vorlage in `templates/server-readme.md` (im Skill-Repo). Pro Server kopieren und befüllen.

### Schritt 2: Anchor-Demo-Query identifizieren

Für jeden Server eine konkrete Frage formulieren, die ein:e Schulamts-Mitarbeiter:in stellen würde. Diese im README prominent.

### Schritt 3: Limits-Workshop

15-Minuten-Workshop pro Server mit Maintainer. Drei Fragen:
- Was funktioniert sehr gut?
- Wo bricht der Server typischerweise?
- Welche Erwartungen sollte der User **nicht** haben?

Resultat als Limits-Sektion.

### Schritt 4: ASCII-Diagramm

Tools wie [Mermaid](https://mermaid.js.org/) oder einfach pure ASCII mit `─`-Box-Drawing-Characters. Bei mehr als 5 Komponenten: zwei Diagramme (Übersicht + Detail).

### Schritt 5: README.de.md synchron halten

Bei jedem PR mit README-Änderungen muss README.de.md auch aktualisiert werden. CI-Hook:

```yaml
- name: Check README parity
  run: |
    grep -E '^## ' README.md | sort > /tmp/en.txt
    grep -E '^## ' README.de.md | sort > /tmp/de.txt
    diff -u /tmp/en.txt /tmp/de.txt || (echo "README sections out of sync"; exit 1)
```

### Effort Estimate

M — 1–3 Tage pro Server für Initial-Doku. Bei portfolio-weitem Roll-out: ~1 Tag pro Server.

### Verification After Fix

- Re-Audit von `OPS-002` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)
