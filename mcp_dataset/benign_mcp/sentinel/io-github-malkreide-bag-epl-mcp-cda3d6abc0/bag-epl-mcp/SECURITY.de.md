# Sicherheitsrichtlinie & Sicherheitslage

[:gb: English Version](SECURITY.md)

`bag-epl-mcp` wurde gegen den internen MCP-Best-Practice-Audit-Katalog
gehärtet. Dieses Dokument fasst die Sicherheitslage zusammen und dokumentiert
die **akzeptierten Risiken** für Kontrollen, die bewusst auf der
Portfolio-/Gateway-Ebene statt innerhalb dieses einzelnen Servers behandelt
werden. Das vollständige Bedrohungsmodell und die Begründung je Kontrolle
finden sich in [`docs/SECURITY.md`](docs/SECURITY.md).

## Schwachstelle melden

Bitte eröffnen Sie einen privaten Bericht über
[GitHub Security Advisories](https://github.com/malkreide/bag-epl-mcp/security/advisories)
oder kontaktieren Sie die in `README.md` genannte verantwortliche Person.
Erstellen Sie für ausnutzbare Schwachstellen **keine** öffentlichen Issues und
geben Sie keine sensiblen Daten an.

## Zusammenfassung der Sicherheitslage

Dies ist ein **rein lesender**, **PII-freier** MCP-Server für **öffentliche
Open Data**. Alle 6 Tools führen ausschliesslich HTTPS-`GET`-Anfragen gegen eine
feste Allow-List Schweizer Bundes-Hosts aus (`sl.bag.admin.ch`,
`www.bag.admin.ch`, `www.fedlex.admin.ch`). Bereits umgesetzte Härtung:

| Bereich | Kontrolle |
|---|---|
| Egress | HTTPS-erzwungene Allow-List nur auf `*.admin.ch`-Hosts, mit IP-Block-Validierung gegen SSRF (SEC-004/021) |
| TLS | DNS-gepinnter Transport: Hostname einmal aufgelöst, IP gepinnt, TLS-/Zertifikatsprüfung gegen den ursprünglichen Hostnamen (SEC-005) |
| Binding | Netzwerk-Transporte standardmässig auf `127.0.0.1`; `0.0.0.0` nur im Container (SEC-016) |
| Transport | stdio (Default, keine Ports) + Streamable HTTP mit CORS-Allow-List (SDK-004) |
| Input | Strikte Pydantic-v2-Validierung an allen Tool-Grenzen (SEC-018) |
| Secrets | Nur Env-Variablen, `.gitignore` schützt `.env`, keine hartkodierten Secrets (SEC-013) |
| Fehler | Upstream-Bodies werden nach stderr geloggt, nie an das Modell weitergegeben (OBS-002) |
| Stdout | Reserviert für den JSON-RPC-Stream; strukturiertes Logging auf stderr festgelegt (OBS-004) |
| Tool-Fläche | 6 rein lesende Tools, `epl_`-Namespace, `readOnlyHint=true` (SEC-014) |
| Container | Mehrstufiges `Dockerfile` läuft als Nicht-Root (UID 10001) mit `HEALTHCHECK` (SEC-007) |

Der jüngste Audit-Lauf (Re-Audit, `2026-06-01`) weist **production-ready** aus:
39 Pass · 0 Fail · 5 partiell (nicht blockierend) · 24 n/a. Den vollständigen
Bericht finden Sie unter [`docs/audit/`](docs/audit/), die Härtungs-Historie im
`CHANGELOG.md`.

## Akzeptierte Risiken (Kontrollen auf Portfolio-Ebene)

Die folgenden Audit-Prüfungen sind innerhalb dieses Servers bewusst **nicht**
vollständig implementiert. Es handelt sich um portfolioweite Anliegen, die am
besten auf einer MCP-Gateway-/Host-Ebene durchgesetzt werden; das Restrisiko
ist hier gering, da der Server rein lesend ist und nur eine feste Menge
vertrauenswürdiger Open-Data-Anbieter erreicht. Die detaillierte Begründung ist
in [`docs/SECURITY.md`](docs/SECURITY.md) festgehalten.

### SEC-009 — Session-Crypto-Binding → N/A (keine Auth)

Es gibt keine Benutzeridentität, an die eine Session gebunden werden könnte:
`bag-epl-mcp` stellt öffentliche Open Data ohne Authentifizierung und ohne
benutzerbezogenen Zustand bereit. Eine Bindung an einen validierten
OAuth-`sub`-Claim ist erst sinnvoll, sobald eine Authentifizierung existiert.

### SEC-014 / SEC-015 — Gateway-Tool-Allow-List & Tool-Poisoning-Erkennung

Die Tool-Fläche ist statisch, rein lesend und im Repository gepflegt (Review
per PR); es gibt keinen Enterprise-Kontext und keine dynamische/entfernte
Tool-Registrierung. Serverübergreifendes Allow-Listing und Pre-Flight-
Tool-Poisoning-Erkennung bleiben eine Gateway-/Host-Verantwortung, die auf
Portfolio-Ebene verfolgt wird.

### SCALE-002 / SCALE-003 — Sticky Sessions (Multi-Instanz)

Phase 1 läuft als **Einzelinstanz**, daher ist kein `Mcp-Session-Id`-Sticky-
Routing erforderlich. Eine Referenz-HAProxy-Stick-Table-Konfiguration für den
Skalierungspfad liegt in [`deploy/haproxy.cfg`](deploy/haproxy.cfg) bei.

## Auslöser für eine Neubewertung

Diese Akzeptanzen sollten erneut geprüft werden, sobald der Server jemals:

- **Schreib**-Fähigkeit erhält oder beginnt, **PII** zu verarbeiten, oder
- ein **Authentifizierungs**-Modell erhält (dann SEC-009 umsetzen: gebundene,
  TTL-versehene, serverseitig invalidierbare Session-IDs und vor dem Merge
  neu auditieren), oder
- Tools **dynamisch** / aus entfernten Quellen registriert, oder
- **horizontal** skaliert wird (dann Sticky Sessions gemäss SCALE-002/003
  aktivieren), oder
- hinter einem gemeinsamen MCP-Gateway aggregiert wird (dann das Tool-Allow-
  Listing und die Tool-Poisoning-Erkennung des Gateways aktivieren).
