# 🛡️ Sicherheitsrichtlinie

[🇬🇧 English Version](SECURITY.md)

## Unterstützte Versionen

Das Projekt befindet sich in `0.x` (Alpha). Nur das jeweils neueste getaggte
Release auf PyPI und der `main`-Branch auf GitHub erhalten Sicherheits-Fixes.
Ältere `0.x`-Releases werden nicht gepatcht.

## Schwachstelle melden

Bitte **kein** öffentliches GitHub-Issue für Sicherheitsfunde eröffnen.

Stattdessen:

1. Ein privates [GitHub Security Advisory](https://github.com/malkreide/hn-tech-signal-mcp/security/advisories/new)
   in diesem Repository eröffnen, oder
2. Den Maintainer (`@malkreide`) per E-Mail kontaktieren — die Adresse ist im
   GitHub-Profil hinterlegt.

Bitte angeben:

- Eine Beschreibung der Schwachstelle und der betroffenen Komponente.
- Einen Reproduktionsfall (Schritte, Payload oder Proof-of-Concept-Code).
- Das erwartete gegenüber dem beobachteten Verhalten.
- Optional einen Vorschlag zur Behebung.

Du erhältst innerhalb von **7 Tagen** eine Eingangsbestätigung. Bestätigte
kritische oder hochgradige Probleme werden in der Regel innerhalb von
**14 Tagen** behoben; mittlere und niedrige werden in den regulären
Release-Rhythmus eingeplant.

## Geltungsbereich

Im Geltungsbereich:

- Das Python-Paket `hn-tech-signal-mcp` (dieses Repository).
- Der MCP-Server selbst (stdio- und Streamable-HTTP-Transport).

Ausserhalb des Geltungsbereichs:

- Die vorgelagerten APIs (HackerNews, Algolia, arXiv, Lobste.rs, GitHub) — diese
  bitte den jeweiligen Betreibern melden.
- Probleme, die eine kompromittierte lokale Maschine, einen böswilligen Betreiber
  oder Social Engineering voraussetzen.

## Audit-Trail

Das Repository dokumentiert vergangene Sicherheitsaudits unter `audits/`. Die
aktuelle Audit-Baseline ist `audits/2026-05-12-hn-tech-signal-mcp/`.
