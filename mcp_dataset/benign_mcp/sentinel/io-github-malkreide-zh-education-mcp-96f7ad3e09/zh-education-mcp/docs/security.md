# Security Posture

## Auth-Modell (Audit SEC-009)

Der Server hat **kein** Auth-Modell (`auth_model: none`) — bewusst, weil:

- die Datenklasse **Public Open Data** ist (aggregierte BISTA-Statistik, keine Personendaten),
- alle Tools **read-only** sind (kein Schreibzugriff, keine Mutation),
- keine Secrets/Tokens verarbeitet werden.

Konsequenz für Sessions: Es gibt keine User-Identität, an die eine Session
kryptografisch gebunden werden könnte. Da der Server zudem **stateless** läuft
(`MCP_STATELESS_HTTP=true`), besteht kein serverseitiger Session-State, der
gekapert werden könnte. Der Impact eines theoretischen Session-Zugriffs ist auf
**öffentliche, read-only Daten** begrenzt.

> **Wenn künftig nicht-öffentliche Daten dazukommen**, ist Authentifizierung
> (OAuth) mit kryptografischer Session-Bindung (`user_id:session_id`) und
> serverseitiger Invalidierung zwingend — siehe Phase 2 in der
> [Roadmap](roadmap.md).

## Defense-in-Depth (umgesetzt)

| Ebene | Massnahme | Referenz |
|-------|-----------|----------|
| Egress | HTTPS-Zwang + Host-Allow-List (jeder Hop) | [network-egress.md](network-egress.md), SEC-004/021 |
| Input | Pydantic v2 `strict=True`, `extra="forbid"`, Range/Length-Constraints | SEC-018 |
| Command | keine `os.system`/`shell=True`/`eval`/`exec` | SEC-020 |
| Errors | Originalfehler nur ins stderr-Log, sanitisierte Client-Meldung | OBS-002 |
| Container | non-root, read-only rootfs, no-new-privileges | [deployment.md](deployment.md), SEC-007 |
| Binding | Default `127.0.0.1`; `0.0.0.0` nur im Container | SEC-016 |
| Trifecta | read-only, keine Exfiltration → max. 1 der 3 Fähigkeiten | SEC-019 |

## Netzwerk-Zugang im Cloud-Betrieb

Der HTTP-Endpoint ist ohne Auth öffentlich erreichbar. Da nur öffentliche
read-only Daten ausgeliefert werden, ist das akzeptabel. Wer den Zugang dennoch
einschränken will, setzt eine Netzwerk-/Plattform-Zugriffskontrolle vor den
Service (IP-Allow-List, VPN, Reverse-Proxy-Auth).
