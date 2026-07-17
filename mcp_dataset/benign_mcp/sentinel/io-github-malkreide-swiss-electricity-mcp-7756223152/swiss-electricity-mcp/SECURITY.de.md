# 🔒 Sicherheitsrichtlinie

🌍 **Read this in your language:** [🇬🇧 English](SECURITY.md)

Teil des **[Swiss Public Data MCP Portfolio](https://github.com/malkreide/swiss-public-data-mcp)**.
Dieses Dokument erklärt, wie Schwachstellen gemeldet werden, und fasst die
Sicherheitslage von `swiss-electricity-mcp` zusammen.

## Unterstützte Versionen

Sicherheitsfixes werden auf die jeweils neueste auf PyPI veröffentlichte Version
angewendet. Bitte aktualisieren Sie immer auf das neueste Release, bevor Sie ein
Problem melden.

| Version | Unterstützt |
|---|---|
| Neueste `0.x` | ✅ |
| Ältere `0.x` | ❌ |

## Eine Schwachstelle melden

**Bitte eröffnen Sie für Sicherheitslücken kein öffentliches GitHub-Issue.**

Melden Sie stattdessen vertraulich über einen dieser Wege:

- **GitHub Security Advisories** — nutzen Sie den Button [*Report a vulnerability*](https://github.com/malkreide/swiss-electricity-mcp/security/advisories/new)
  unter dem Reiter **Security** des Repositorys (bevorzugt).
- **E-Mail** — `hayal.oezkan@gmail.com` mit der Betreffzeile
  `[SECURITY] swiss-electricity-mcp`.

Bitte fügen Sie bei:

- eine Beschreibung des Problems und seiner möglichen Auswirkung,
- Schritte zur Reproduktion (wenn möglich ein minimaler Proof of Concept),
- betroffene Version(en) und Umgebungsdetails.

**Reaktionsziele:** Bestätigung innerhalb von **72 Stunden**, eine erste
Einschätzung innerhalb von **7 Tagen** und ein mit Ihnen abgestimmter Zeitplan für
Fix/Offenlegung. Bitte geben Sie uns angemessene Zeit für einen Fix, bevor Sie
etwas öffentlich machen.

## Sicherheitslage

`swiss-electricity-mcp` ist ein **schreibgeschützter** (read-only) MCP-Server, der
ausschliesslich öffentliche Schweizer Open Government Data bereitstellt.
Wesentliche Eigenschaften:

- **Keine Authentifizierung, keine Geheimnisse.** Alle vier Upstreams sind anonym
  zugängliche öffentliche OGD-Endpunkte — es gibt keine API-Schlüssel, Tokens oder
  Zugangsdaten im Code, in der Umgebung oder im Deployment.
- **Keine privaten Daten, keine PII.** Es werden nur öffentliche Open Data
  (CC0 / CC BY 4.0) gelesen.
- **Egress-Allow-List.** `assert_url_allowed()` kontrolliert *jede* ausgehende
  Anfrage: HTTPS wird erzwungen und jeder Host ausserhalb eines festen
  `frozenset` von vier offiziellen Hosts wird abgelehnt. Cloud-Metadaten-IPs
  (`169.254.169.254`) und Nicht-HTTPS-Schemata werden konstruktionsbedingt
  abgewiesen. Siehe [`docs/network-egress.md`](docs/network-egress.md).
- **Kein Schreib- oder Exfiltrationspfad.** Alle 12 Tools sind read-only
  (`readOnlyHint=true`); es gibt keine Schreib-, Mail- oder Webhook-Tools.
- **«Lethal Trifecta» konstruktionsbedingt sicher.** Höchstens eine von
  {private Daten, nicht vertrauenswürdige Inhalte, Exfiltrationsfähigkeit} ist
  nennenswert vorhanden. Siehe [`docs/security-posture.md`](docs/security-posture.md).
- **Supply-Chain-Hygiene.** Reiner Python-Build via `hatchling` ohne
  pre/postinstall-Hooks; Abhängigkeiten sind gepinnt und werden via Dependabot
  aktualisiert; Releases werden via OIDC **Trusted Publisher** auf PyPI
  veröffentlicht (kein langlebiges Token). Gitleaks (`secret-scan.yml`) läuft bei
  jedem Push/PR.

## Härtungsempfehlungen für Betreiber

- Im HTTP-Modus ist der Host standardmässig `127.0.0.1`. Setzen Sie
  `SWISS_ELECTRICITY_HOST=0.0.0.0` nur **innerhalb eines Containers**, nie auf einem
  Entwicklerrechner (NeighborJack).
- Ergänzen Sie als Defense-in-Depth eine Egress-Beschränkung auf Netzwerkebene
  (Kubernetes-`NetworkPolicy`, Plattform-Egress-Regeln oder einen Egress-Proxy).
- Setzen Sie niemals `SWISS_ELECTRICITY_CORS_ORIGINS=*`; listen Sie explizite
  Origins auf.

Die vollständige Sicherheitsbegründung finden Sie in
[`docs/security-posture.md`](docs/security-posture.md) und
[`docs/network-egress.md`](docs/network-egress.md).
