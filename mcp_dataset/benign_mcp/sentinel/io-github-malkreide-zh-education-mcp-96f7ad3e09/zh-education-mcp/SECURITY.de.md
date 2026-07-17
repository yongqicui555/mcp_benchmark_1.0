# 🔒 Sicherheitsrichtlinie

[🇬🇧 English Version](SECURITY.md)

Vielen Dank, dass du hilfst, `zh-education-mcp` und seine Nutzer sicher zu halten.

## Unterstützte Versionen

Sicherheitsfixes werden für die jeweils aktuellste veröffentlichte Version
bereitgestellt. Bitte stelle sicher, dass du die neueste Version verwendest,
bevor du ein Problem meldest.

| Version | Unterstützt |
|---------|-------------|
| 0.2.x   | ✅          |
| < 0.2   | ❌          |

## Eine Sicherheitslücke melden

**Bitte eröffne für Sicherheitslücken keine öffentlichen GitHub-Issues.**

Melde sie stattdessen vertraulich:

- **E-Mail:** hayal.oezkan@gmail.com
- Oder über GitHubs [private Vulnerability-Reporting](https://github.com/malkreide/zh-education-mcp/security/advisories/new)

Bitte gib an:

- eine Beschreibung der Schwachstelle und ihrer möglichen Auswirkungen,
- Schritte zur Reproduktion (nach Möglichkeit ein Proof of Concept),
- betroffene Version(en) und Umgebung.

Du erhältst innerhalb von **5 Werktagen** eine Eingangsbestätigung. Wir halten
dich über den Fortschritt bei der Behebung auf dem Laufenden und koordinieren
die Offenlegung mit dir.

## Sicherheits-Posture

`zh-education-mcp` ist darauf ausgelegt, seine Angriffsfläche zu minimieren:

- **Nur lesend:** Alle Tools sind `readOnlyHint: true` — der Server kann keine
  Daten verändern, löschen oder schreiben.
- **Keine Authentifizierung / keine Secrets:** Die BISTA-API ist vollständig
  öffentlich; es werden keine API-Schlüssel, Tokens oder Zugangsdaten
  gespeichert oder übertragen.
- **Keine Personendaten:** BISTA-Statistiken sind aggregiert — es werden keine
  individuellen Schülerdaten offengelegt oder zugänglich gemacht.
- **Defense-in-Depth:** HTTPS-Zwang + Host-Allow-List beim Egress, strikte
  Pydantic-v2-Input-Validierung, sanitisierte Fehlermeldungen und ein
  gehärteter Container (non-root, read-only rootfs, `no-new-privileges`).

Die vollständige technische Security-Posture, akzeptierte Risiken und das
Netzwerk-Egress-Modell sind dokumentiert in:

- [`docs/security.md`](docs/security.md) — Security-Posture & Defense-in-Depth
- [`docs/network-egress.md`](docs/network-egress.md) — Egress-Allow-List
- [`docs/secret-management.md`](docs/secret-management.md) — Secret-Handling
- [`docs/accepted-risks.md`](docs/accepted-risks.md) — akzeptierte Risiken

---

> 🇨🇭 Teil des [Swiss Public Data MCP Portfolios](https://github.com/malkreide)
