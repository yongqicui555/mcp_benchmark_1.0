# ADR-002: Skalierung & Stateful Load Balancing

## Status
Akzeptiert, 2026-05-30

## Kontext
Streamable HTTP ist zustandsbehaftet; bei mehreren Replicas muss eine
MCP-Session konsistent zum selben Backend geroutet werden (SCALE-002/003).
Aktuell läuft `parlament-mcp` als **Single Instance** (lokal stdio bzw. eine
Railway-Instanz).

## Entscheidung
- **Single-Instance-Betrieb** braucht kein Sticky-Routing — die Session lebt im
  einzigen Prozess. Das ist der aktuelle Stand.
- Für **horizontale Skalierung (>1 Replica)** sind zwei erprobte Pfade
  vorbereitet und versioniert, aber noch nicht aktiviert:
  1. **Sticky Sessions am Edge-LB** auf `Mcp-Session-Id`
     (`deploy/k8s/service-ingress.yaml`, `deploy/haproxy.cfg`).
  2. **Shared-State-Session-Store** (Redis) — Option für Phase 3.

Da alle Tools zustandslose Read-Operationen sind (keine Subscriptions, keine
Per-Session-Daten), ist der Impact eines Pod-Switches gering (Client
re-initialisiert); die Sticky-Variante ist dennoch der empfohlene erste Schritt.

## Konsequenzen
- Aktivierung der Sticky-Konfiguration ist eine reine Deploy-Änderung (Manifeste
  liegen bereit), kein Code-Change.
- Vor Aktivierung von Schreibzugriffen (Phase 3) ist ein Shared-State-Store mit
  TTL verpflichtend.
