# Sicherheitsrichtlinie & Sicherheitslage

[🇬🇧 English Version](SECURITY.md)

`parlament-mcp` wurde gegen den internen MCP-Best-Practice-Audit-Katalog
gehärtet. Dieses Dokument fasst die Sicherheitslage zusammen und dokumentiert die
**akzeptierten Risiken** für Kontrollen, die bewusst auf der Portfolio-/Gateway-Ebene
statt innerhalb dieses einzelnen Servers behandelt werden.

## Schwachstelle melden

Bitte eröffnen Sie ein privates Security Advisory im GitHub-Repository oder
kontaktieren Sie die in `README.md` genannte verantwortliche Person. Erstellen Sie
für ausnutzbare Schwachstellen **keine** öffentlichen Issues.

## Zusammenfassung der Sicherheitslage

Dies ist ein **rein lesender**, **PII-freier** MCP-Server für **öffentliche Open
Data**. Alle 6 Tools stellen ausschliesslich lesende OData-Abfragen an den
Curia-Vista-Endpoint (`ws.parlament.ch`). Bereits umgesetzte Härtungsmassnahmen:

| Bereich | Kontrolle |
|---|---|
| Egress | HTTPS-erzwungene Allow-List ausschliesslich für `ws.parlament.ch` (`security.ALLOWED_HOSTS`), pro Request via `assert_host_allowed()` geprüft (SEC-021) |
| Netzwerk | Kubernetes-`NetworkPolicy` erlaubt nur HTTPS/443- + DNS-Egress; Cloud-Metadata- und RFC1918-Bereiche blockiert (SEC-021) |
| Binding | Netzwerk-Transporte binden standardmässig an `127.0.0.1`; `0.0.0.0` nur in einem erkannten Container, sonst wird eine NeighborJack-Warnung geloggt (SEC-016) |
| Transport | Streamable HTTP mit CORS, das nur `Mcp-Session-Id` exponiert (SDK-004) |
| Auth | Optionale, opt-in Bearer-Tokens über `MCP_BEARER_TOKENS`; die Identität kommt aus dem validierten Token, nicht aus einem spoofbaren Session-Header (SEC-009) |
| Input | Pydantic-v2-Strict-Validierung an allen Grenzen (SEC-018) |
| Secrets | Keine Secrets verwendet (öffentliche API); `gitleaks` läuft in CI als Regressionsschutz; PyPI-Releases nutzen OIDC-Trusted-Publishing (ARCH-005/SEC-013) |
| Fehler | Menschenlesbare deutsche Fehlertexte; Upstream-Antworten werden nach stderr geloggt, niemals an das Modell weitergegeben (OBS-002) |
| Stdout | Reserviert für den JSON-RPC-Stream; strukturiertes Logging fest auf stderr (OBS-004) |
| Tool-Allow-List | Serverseitige Default-Deny-Allow-List über `gateway.filter_allowed_tools()` (SEC-014) |
| Tool-Integrität | SHA-256-Tool-Hash-Pinning in CI gegen `tool-hashes.json` verifiziert (SEC-022) |

Die vollständige Sicherheitsdarstellung (Lethal-Trifecta-Bewertung,
Egress-Allow-List, Gateway-Härtung) finden Sie in
[`docs/security.md`](docs/security.md), die Audit-Berichte unter `audits/` und die
Härtungshistorie in [`CHANGELOG.md`](CHANGELOG.md).

## Lethal-Trifecta-Bewertung (SEC-019)

Ein Server wird erst gefährlich, wenn er **alle drei** Fähigkeiten von Simon
Willisons «Lethal Trifecta» vereint:

| Fähigkeit | Status | Begründung |
|---|:--:|---|
| Zugriff auf private Daten | ❌ Nein | Ausschliesslich öffentliche Open Data (Curia Vista). Keine PII, keine Verwaltungs-Innendaten. |
| Exposition gegenüber untrusted Content | ⚠️ Begrenzt | Liest nur die feste, vertrauenswürdige Curia-Vista-API; keine User-Uploads, kein beliebiges Web-Scraping. |
| Externe Kommunikation / Write | ❌ Nein | Read-only; alle Tools `readOnlyHint: true`. Kein Mail-/Webhook-/POST-Versand. |

**Trifecta-Score: ~1 von 3 → sicher.** Eine Datenexfiltration via
Prompt-Injection ist strukturell nicht möglich: Der Server liest weder private
Daten noch sendet er Daten nach aussen.

## Akzeptierte Risiken (Kontrollen auf Portfolio-Ebene)

Die folgenden Audit-Prüfungen sind **bewusst nicht** vollständig innerhalb dieses
Servers implementiert. Es handelt sich um portfolioweite Belange, die am besten auf
einer MCP-Gateway-/Host-Ebene durchgesetzt werden; das Restrisiko ist hier gering, da
der Server rein lesend ist und nur einen einzigen vertrauenswürdigen
Open-Data-Anbieter erreicht.

### SEC-009 — Session-Krypto-Bindung → optional (keine zwingende Auth)

**Status:** in Phase 1 optional. `parlament-mcp` stellt öffentliche Open Data ohne
zwingende Authentifizierung bereit, sodass es standardmässig keine Benutzeridentität
gibt, an die eine Session gebunden werden könnte. Das Repo liefert bereits
`auth.SessionSigner` (HMAC-SHA256, TTL, Revocation, User-Bindung) für Deployments,
die Bearer-Auth aktivieren; die Bindung wird in Phase 3 (Write) verpflichtend — siehe
[`docs/roadmap.md`](docs/roadmap.md).

### SEC-015 — Pre-Flight-Erkennung von Tool-Poisoning

**Status:** akzeptiertes Risiko (Portfolio-Ebene) — mit lokaler Schutzmassnahme.
Tool-Poisoning (bösartige Tool-Beschreibungen / Rug-Pulls) ist ein Lieferketten- und
Host-seitiges Problem. Die Tool-Definitionen dieses Servers sind versionskontrolliert,
im Repository verfasst und werden per PR geprüft; es gibt keine dynamische/entfernte
Tool-Registrierung. Lokal erkennt **SEC-022 Tool-Hash-Pinning** (`tool-hashes.json`)
jegliche Veränderung der Tool-Oberfläche in CI, und `gateway.scan_tool_definition()`
bietet wiederverwendbare Poisoning-Erkennung für den Multi-Server-Fall. Die
serverübergreifende Poisoning-Erkennung bleibt eine Gateway-/Host-Verantwortung, die
auf Portfolio-Ebene verfolgt wird.

## Re-Evaluierungs-Auslöser

Diese Akzeptanzen sollten neu bewertet werden, falls der Server jemals:

- **Schreib**-Funktionalität erhält oder beginnt, **PII** zu verarbeiten, oder
- ein **zwingendes Authentifizierungs**-Modell hinzufügt (dann SEC-009 durchsetzen:
  gebundene, TTL-versehene, serverseitig invalidierbare Session-IDs und Re-Audit vor
  dem Merge), oder
- Tools **dynamisch** / aus entfernten Quellen registriert, oder
- hinter einem gemeinsamen MCP-Gateway aggregiert wird (dann das Tool-Allow-Listing
  und die Tool-Poisoning-Erkennung des Gateways aktivieren).
