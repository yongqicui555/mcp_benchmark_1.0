# Sicherheitsrichtlinie

[🇬🇧 English Version](SECURITY.md)

Dieses Dokument beschreibt das Sicherheitsmodell von **bakom-mcp** und wie eine Schwachstelle verantwortungsvoll gemeldet werden kann. Der Server ist Teil des [Swiss Public Data MCP Portfolios](https://github.com/malkreide).

---

## Unterstützte Versionen

Sicherheitsupdates werden für die jeweils neueste veröffentlichte Minor-Version bereitgestellt. Ältere Versionen werden nicht gepflegt — bitte vor einer Meldung aktualisieren.

| Version | Unterstützt        |
|---------|--------------------|
| 2.x     | ✅ Ja              |
| < 2.0   | ❌ Nein            |

---

## Eine Schwachstelle melden

**Bitte eröffne für Sicherheitslücken kein öffentliches GitHub-Issue.**

Melde sie vertraulich über GitHubs [private Vulnerability-Reporting](https://github.com/malkreide/bakom-mcp/security/advisories/new) (**Security → Report a vulnerability**). So bleiben die Details vertraulich, bis ein Fix verfügbar ist.

Bitte gib an:

- Eine Beschreibung der Schwachstelle und ihrer möglichen Auswirkung
- Schritte zur Reproduktion (Proof of Concept, betroffenes Tool, Eingabewerte)
- Die betroffene Version (`bakom-mcp --version` oder `pip show bakom-mcp`)
- Einen Vorschlag zur Behebung, falls bekannt

**Reaktionszeiten:**

- **Eingangsbestätigung:** innerhalb von 72 Stunden
- **Erste Einschätzung:** innerhalb von 7 Tagen
- **Fix / koordinierte Offenlegung:** je nach Schweregrad, in der Regel innerhalb von 30 Tagen

Bitte gewähre eine angemessene Frist für einen Fix, bevor du Details öffentlich machst. Meldende, die diesen Prozess einhalten, werden in den Release-Notes genannt, sofern sie nicht anonym bleiben möchten.

---

## Sicherheitsmodell

**bakom-mcp** ist auf eine minimale Angriffsfläche ausgelegt. Per Design gilt für den Server:

- ✅ Er ist **read-only** (`readOnlyHint: true`) — es gibt keine Schreib-, Lösch- oder Mutations-Tools.
- ✅ Er benötigt **keine Authentifizierungs-Tokens oder Secrets** — alle Datenquellen sind öffentliche Open Government Data (OGD).
- ✅ Er beschränkt ausgehenden Verkehr auf eine **Egress-Allow-List** auf Code-Ebene mit den bekannten BAKOM-/Bund-Datenquellen-Hosts ([`src/bakom_mcp/server.py`](src/bakom_mcp/server.py)).
- ✅ Er validiert alle Koordinaten-Eingaben gegen die **Schweizer WGS84-Bounding-Box** (lat 45.8–47.9, lon 5.9–10.6) via Pydantic.
- ✅ Er greift **nicht** auf das lokale Dateisystem zu (kein Path-Traversal-Vektor).
- ✅ Er führt **keine** Shell-Befehle oder beliebigen Code aus (kein `subprocess` / `os.system` / `eval`).
- ✅ Er cached oder persistiert **keine** User-Eingaben über Calls hinweg.
- ✅ Er erzwingt Abfrage-Limits (max. 50 Antennen, max. 20 Standorte, max. 50 RTV-Resultate) und ein Timeout von 20 Sekunden pro vorgelagertem Aufruf.

### HTTP- / Cloud-Deployment

Beim Betrieb mit HTTP-Transport (`--http`):

- Der Server bindet standardmässig auf `127.0.0.1`; das Binden auf `0.0.0.0` loggt eine Warnung und sollte nur in vertrauenswürdigen Netzen erfolgen.
- CORS ist **deaktiviert**, sofern `BAKOM_MCP_CORS_ORIGINS` nicht explizit konfiguriert wird.
- Für öffentliche Erreichbarkeit sind TLS und CORS an einem Reverse-Proxy (Caddy, Traefik, nginx) zu terminieren.

### Container-Härtung

Das bereitgestellte Docker-Image läuft als **non-root** (UID 10001), nutzt ein **read-only-Dateisystem**, entzieht **alle Linux-Capabilities**, verbietet **Privilege-Escalation** (`no-new-privileges`) und wendet Memory-/CPU-/PID-Limits an (siehe [`docker-compose.yml`](docker-compose.yml)).

### Lieferkette (Supply Chain)

- Abhängigkeiten sind in [`pyproject.toml`](pyproject.toml) mit Versions-Obergrenzen gepinnt.
- Ein [Secret-Scanning-Workflow](.github/workflows/secret-scan.yml) läuft in der CI, um versehentliche Credential-Commits zu verhindern.
- Unabhängige Security-Audit-Berichte sind unter [`audits/`](audits/) veröffentlicht.

---

## Geltungsbereich

Im Geltungsbereich:

- Der `bakom-mcp`-Server-Code in diesem Repository
- Input-Validierung, Egress-Kontrollen und die HTTP-Transport-Konfiguration

Ausserhalb des Geltungsbereichs:

- Schwachstellen bei vorgelagerten Datenanbietern (geo.admin.ch, opendata.swiss, rtvdb.ofcomnet.ch) — diese bitte den jeweiligen Betreibern melden
- Die Korrektheit oder Verfügbarkeit der Open Data selbst
- Allgemeine Netzwerk-/DoS-Probleme gegen öffentliche Drittanbieter-APIs

---

*Danke, dass du hilfst, bakom-mcp und das Swiss Public Data MCP Portfolio sicher zu halten.*
