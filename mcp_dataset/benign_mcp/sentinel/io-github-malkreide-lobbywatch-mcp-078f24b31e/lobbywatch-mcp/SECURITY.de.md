# Sicherheitsrichtlinie & -posture

[🇬🇧 English version](SECURITY.md)

`lobbywatch-mcp` wurde gegen den internen MCP-Best-Practice-Audit-Katalog
gehärtet. Dieses Dokument fasst die Sicherheits-Posture zusammen und hält die
**akzeptierten Risiken** für jene Kontrollen fest, die bewusst auf der
Portfolio-/Gateway-Ebene statt in diesem einzelnen Server behandelt werden.

## Schwachstellen melden

Bitte Sicherheitsprobleme **vertraulich** melden — für eine ausnutzbare
Schwachstelle kein öffentliches Issue eröffnen:

- Ein [GitHub Security Advisory](https://github.com/malkreide/lobbywatch-mcp/security/advisories/new) eröffnen, oder
- den Maintainer kontaktieren ([malkreide](https://github.com/malkreide)).

Du erhältst eine Eingangsbestätigung; Fix und Offenlegungs-Zeitplan stimmen
wir gemeinsam mit dir ab.

## Posture-Zusammenfassung

Das jüngste Re-Audit (`2026-05-09`, Katalog v1.0.0) ergab **41 pass /
0 fail / 1 partial / 2 todo** über 44 anwendbare Checks, mit
`production_ready: true` und ohne blockierende Findings. Zentrale Kontrollen:

- **SSRF-Prävention.** Ein einziger `httpx.AsyncClient` mit
  `follow_redirects=False`, eine IP-Blockliste für RFC1918-, Link-local-,
  Loopback- und Cloud-Metadata-Bereiche, und ein httpx-Event-Hook, der das
  Ziel bei jedem Request neu auflöst (DNS-Rebinding-/TOCTOU-Schutz).
- **Egress-Allow-List.** Ausgehender Verkehr ist auf die vertrauenswürdigen
  Lobbywatch-Hosts beschränkt (`cms.lobbywatch.ch`-Dump + `dataIF`-REST) auf
  Code-Ebene; Network-Layer-Härtung ist in `docs/deployment.md` dokumentiert.
- **Sicherer Bind-Default.** HTTP-/SSE-Transports binden standardmässig an
  `127.0.0.1`; `0.0.0.0` erfordert explizites Opt-in (NeighborJack-Schutz).
- **Strikte Input-Validierung.** Tool-Argumente sind typisiert und begrenzt
  (Allow-List für Kriterien, gedeckeltes `limit`, längengeprüfte Queries) an
  der Pydantic-Boundary.
- **Keine Command-/SQL-Oberfläche.** Read-only-Server — kein `os.system`,
  `shell=True`, `eval` und keine Schreibpfade; Daten stammen nur aus dem
  JSON-Dump und `dataIF`.
- **Maskierte Fehler.** Upstream-Response-Bodies und Stacktraces werden nie an
  das Modell weitergegeben; strukturiertes Logging geht nach stderr.
- **Gehärteter Container.** Multi-Stage, non-root,
  read-only-rootfs-kompatibles `Dockerfile`.
- **Namespace-Präfix.** Alle Tools tragen das `lobbywatch_`-Präfix, um
  Kollisionen / Rug-Pull zwischen Servern zu verhindern.
- **Keine Secrets.** `auth_model = none` — keine API-Keys, keine
  Secret-Storage-Angriffsfläche (Phase 1 No-Auth-First).

## Lethal-Trifecta-Bewertung (SEC-019)

Gemessen an Simon Willisons Framework erreicht dieser Server etwa **1 von 3**:

1. **Zugriff auf private Daten** — *Nein.* Nur öffentliche, CC-BY-SA-4.0-Daten.
2. **Exposition gegenüber nicht vertrauenswürdigem Inhalt** — *Begrenzt.*
   Liest nur von festen, vertrauenswürdigen Lobbywatch-Hosts.
3. **Fähigkeit zur Exfiltration / externen Kommunikation** — *Nein.*
   Read-only, keine Schreib-Tools, kein ausgehender Seitenkanal.

Damit ist Datenexfiltration über Prompt Injection strukturell unmöglich: Der
Server kann nicht schreiben und hat keinen Pfad, um Daten irgendwohin ausser
zurück an den anfragenden Client zu senden.

## Akzeptierte Risiken (Kontrollen auf Portfolio-Ebene)

Zwei Checks bleiben **todo**, weil sie Deployment- bzw. Client-seitige Belange
sind, die bewusst auf die Portfolio-/Gateway-Ebene verlagert und nicht in
diesem read-only Server dupliziert werden.

### SEC-014 — Tool-Allow-Listing → Gateway

Tool-Allow-Listing wird auf der Deployment-/Gateway-Ebene durchgesetzt, nicht
im Server. Das Restrisiko ist gering: Der Server ist read-only, stellt
öffentliche Open Data bereit und erfordert keine Authentifizierung.

### SEC-015 — Pre-flight-Tool-Poisoning-Erkennung

Tool-Poisoning-Erkennung ist eine Client-seitige Verantwortung und für den
Server selbst ausserhalb des Scopes. Das `lobbywatch_`-Namespace-Präfix bietet
Defense-in-Depth gegen Tool-Namens-Kollisionen.

Das verwandte **SEC-009** (Session-Crypto-Binding) ist für dieses Trust-Modell
erfüllt: Der Server kennt kein Benutzerkonzept, daher kann `Mcp-Session-Id`
nicht an eine `user_id` gebunden werden. Das ist für No-Auth-First-read-only
Public-Data akzeptabel und wird hier als explizites Trust-Modell dokumentiert.

## Re-Evaluations-Trigger

Diese Risikoakzeptanzen sind neu zu bewerten, sobald der Server:

- Schreibfähigkeiten oder ein nebenwirkungsbehaftetes Tool erhält,
- personenbezogene / nicht-öffentliche Daten verarbeitet,
- verpflichtende Authentifizierung oder Pro-Benutzer-Sessions einführt,
- Tools dynamisch registriert, oder
- hinter einem geteilten Multi-Tenant-Gateway betrieben wird.
