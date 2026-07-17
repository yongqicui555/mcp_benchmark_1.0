# Network Egress

Defense-in-Depth für ausgehende Verbindungen (Audit SEC-004 / SEC-021).

## Code-Layer (implementiert)

Die erlaubten Ziel-Hosts sind als unveränderliches `frozenset` im Code definiert
(`ALLOWED_HOSTS` in `server.py`) — **nicht** zur Laufzeit oder via ENV mutierbar:

```
ALLOWED_HOSTS = frozenset({"www.bista.zh.ch"})
```

Ein httpx-`request`-Event-Hook (`_egress_guard`) prüft **jeden** ausgehenden
Request — auch Redirect-Hops — und erzwingt:

- Schema `https` (kein Cleartext)
- Host ∈ `ALLOWED_HOSTS`

Damit sind klassische SSRF (kein user-kontrollierter Host) **und**
Redirect-basierte SSRF (Umleitung auf Metadata-IPs wie `169.254.169.254`)
blockiert.

## Network-Layer (Deployment-Verantwortung)

Im Cloud-Deployment ist ergänzend eine Netzwerk-Egress-Kontrolle zu setzen
(Defense-in-Depth, falls der Code-Layer kompromittiert wird):

- **Render/Railway:** Egress auf `www.bista.zh.ch:443` beschränken (sofern Plattform-Egress-Rules unterstützt werden).
- **Kubernetes:** `NetworkPolicy` mit `egress`-Allow nur für den BISTA-Host + DNS (Port 53).
- **DNS** muss erlaubt bleiben, sonst schlägt die Hostname-Auflösung still fehl.

## Allow-List erweitern

Neue Datenquellen werden durch Ergänzen von `ALLOWED_HOSTS` im Code (per PR,
mit Review) freigeschaltet — bewusst kein Runtime-Mechanismus.

## DNS-Validierung (SEC-005)

Vor jedem ausgehenden Request löst `_resolve_and_validate()` den Host **einmal**
auf und prüft **alle** resolved IPs gegen eine Blocklist (private, loopback,
link-local inkl. Cloud-Metadata `169.254.169.254`, multicast, reserved,
unspecified). Löst der erlaubte Host auf eine interne IP auf (DNS-Rebinding),
wird vor dem Verbindungsaufbau hart abgebrochen.

## Bekanntes Restrisiko

- **Socket-Level-Pinning:** Die Validierung prüft die aufgelösten IPs, verbindet
  danach aber über den Standard-httpx-Resolver (ein theoretisches TOCTOU-Fenster
  zwischen Validierungs-Lookup und Connect-Lookup bleibt). Das Restrisiko ist
  durch die Single-Host-Allow-List (ein vertrauenswürdiger Host) gering. Echtes
  Socket-Pinning (Connect zur exakt validierten IP) ist als Folge-Härtung
  vorgemerkt; es konnte in der CI-Sandbox nicht live verifiziert werden.
