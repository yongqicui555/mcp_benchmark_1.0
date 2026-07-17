# Deployment

`zh-education-mcp` läuft in zwei Modi:

| Modus | Befehl | Use-Case |
|-------|--------|----------|
| **stdio** (Default) | `zh-education-mcp` | Lokal, Claude Desktop |
| **Streamable HTTP** | `MCP_TRANSPORT=streamable-http zh-education-mcp` | Cloud, Browser (claude.ai) |

Konfiguration erfolgt ausschliesslich über Umgebungsvariablen (Präfix `MCP_`):

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `MCP_TRANSPORT` | `stdio` | `stdio` · `streamable-http` · `sse` |
| `MCP_HOST` | `127.0.0.1` | Bind-Adresse. **Nur im Container** auf `0.0.0.0` setzen (SEC-016) |
| `MCP_PORT` | `8000` | HTTP-Port |
| `MCP_STATELESS_HTTP` | `true` | Stateless-Modus (siehe Load Balancing) |
| `MCP_CORS_ORIGINS` | `https://claude.ai` | Komma-separierte Origin-Allow-List (keine Wildcard in Prod) |

> CLI-Flags `--http`/`--sse`/`--port`/`--host` überschreiben die ENV-Werte (Abwärtskompatibilität).

## Container

```bash
docker build -t zh-education-mcp .
docker compose up        # mit Resource-Limits aus docker-compose.yml
```

Das Image ist Multi-Stage (`python:3.12-slim`), läuft als **non-root** (`uid 10001`),
mit `read_only`-Rootfs, `no-new-privileges` und einem `/health`-HEALTHCHECK
(SEC-007, SCALE-004). Resource-Limits (Memory/CPU/FD) sind in `docker-compose.yml`
gesetzt (SCALE-006) und dienen für Render/Railway als Vorlage.

## Load Balancing & Sessions (SCALE-002 / SCALE-003)

Der Server ist **read-only** und hält **keinen serverseitigen Session-State**
(`MCP_STATELESS_HTTP=true`). Konsequenz:

- **Keine Sticky Sessions / kein Mcp-Session-Id-Routing nötig.** Jeder Request
  ist unabhängig; ein Standard-Round-Robin-Load-Balancer (Render/Railway/K8s
  Ingress in Default-Konfiguration) verteilt korrekt über mehrere Instanzen.
- **Kein Shared-State-Store (Redis o.ä.) erforderlich**, weil keine Session
  zwischen Requests fortbesteht.
- **Failover** ist trivial: fällt eine Instanz aus, kann der nächste Request
  ohne Affinität auf einer beliebigen anderen Instanz bedient werden.

> Sollte künftig zustandsbehafteter (stateful) Betrieb nötig werden
> (`MCP_STATELESS_HTTP=false`), ist Sticky-Session-Routing auf `Mcp-Session-Id`
> am Edge-LB **oder** ein gemeinsamer Session-Store mit TTL einzuführen. Solange
> der Server read-only und stateless ist, ist das bewusst nicht implementiert.

## Health

`GET /health` → `200 {"status":"ok","service":"zh-education-mcp"}` — für
Load-Balancer-Probes und den Docker-HEALTHCHECK.

## Beispiel: Render.com

1. Repo verbinden, Runtime „Docker".
2. Render setzt `PORT` — entsprechend `MCP_PORT` mappen (oder `MCP_PORT=8000`).
3. Endpoint in claude.ai: `https://<app>.onrender.com/mcp` (Streamable HTTP).

## Observability — OpenTelemetry (opt-in, OBS-006)

Tracing ist standardmäßig **aus** (kein Overhead im stdio-Default). Aktivierung:

```bash
pip install "zh-education-mcp[otel]"
export MCP_OTEL_ENABLED=true
export OTEL_EXPORTER_OTLP_ENDPOINT="https://otel-collector:4318"   # OTLP/HTTP
export OTEL_SERVICE_NAME="zh-education-mcp"
```

Pro Tool-Call entsteht ein Span `mcp.tool/<name>` mit `mcp.tool.name` und
`mcp.tool.result.is_error` (bewusst minimal, kein PII). Ausgehende
httpx-Requests werden als Child-Spans auto-instrumentiert. Ist das SDK nicht
installiert oder die ENV-Var nicht gesetzt, läuft der Server unverändert ohne
Tracing.
