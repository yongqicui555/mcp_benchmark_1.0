# Deployment

Guidance for running `lobbywatch-mcp` outside `stdio` / Claude Desktop. All
recommendations here close audit findings SEC-007 (sandboxing),
SCALE-004 (containerisation), and SCALE-006 (resource limits).

## Trust model recap

`lobbywatch-mcp` ships **without authentication** (Phase 1, No-Auth-First).
That is fine for local `stdio` use because the MCP client (Claude Desktop)
is the trust boundary. The moment you switch to HTTP/SSE, the network
becomes the attack surface — the server itself does **not** authenticate
callers. You must therefore put an auth-enforcing layer in front of the
container before exposing it to anything beyond loopback.

In practice this means one of:

- A reverse proxy with mTLS or OAuth (Caddy, nginx, Traefik, Tyk, Kong).
- An MCP-aware gateway (where applicable) that forwards `Mcp-Session-Id`.
- A private network (VPN, service mesh) where every caller is already
  authenticated upstream.

## Container

A multi-stage `Dockerfile` is included at the repo root. It produces a
small Python-slim runtime image with:

- Non-root user (`uid:gid = 1000:1000`)
- No build toolchain in the final stage
- Read-only-rootfs compatibility (cache directory under
  `/home/lobbywatch/.cache/lobbywatch-mcp`, intended to be mounted as
  `tmpfs`)
- Default `LOBBYWATCH_MCP_TRANSPORT=http` and `HOST=0.0.0.0` so the server
  binds to the container's own network namespace; the **host-side bind**
  must restrict reachability (see compose example).

### Build

```bash
docker build -t lobbywatch-mcp:0.2.0 .
```

### Run (one-off)

```bash
docker run --rm -p 127.0.0.1:8000:8000 \
    --read-only \
    --cap-drop ALL \
    --security-opt no-new-privileges \
    --tmpfs /home/lobbywatch/.cache:size=128M,uid=1000,gid=1000,mode=0700 \
    --memory 512m --cpus 0.5 \
    lobbywatch-mcp:0.2.0
```

### docker-compose

A complete worked example, including resource limits and tmpfs caching,
lives at [`deploy/docker-compose.example.yml`](../deploy/docker-compose.example.yml).
Copy it into your stack and adjust:

```bash
cp deploy/docker-compose.example.yml docker-compose.yml
docker compose up -d
```

## Resource limits (audit SCALE-006)

The weekly dump occupies ~17 MB on disk (compressed) and ~80 MB resident
once parsed into Python objects. With async workloads + Pydantic models
the steady-state working set is around 120–180 MB. Recommended limits:

| Resource | Request | Limit | Rationale |
|---|---|---|---|
| Memory | 256 MiB | 512 MiB | Dump + async + headroom |
| CPU | 0.1 | 0.5 | Reads are linear scans over 245 MPs |
| File descriptors | – | 1024 (default) | Mostly idle keep-alive sockets |

If the cache TTL is short or the live `dataIF` endpoint is hit often,
double the CPU limit before the memory limit.

## Stateful HTTP / Streamable transport (audit SCALE-002, SCALE-003)

`streamable-http` and `sse` transports use the `Mcp-Session-Id` header to
correlate the client's request lifecycle with the server-side session.
Round-robin load balancers will break that continuity — clients
experience sporadic session loss and tools fail mid-call.

When deploying behind a load balancer, configure stick-tables on the
header. HAProxy example:

```haproxy
frontend mcp_in
    bind *:443 ssl crt /etc/haproxy/certs/lobbywatch.pem
    default_backend mcp_be

backend mcp_be
    balance roundrobin
    stick-table type string len 64 size 100k expire 30m
    stick on req.hdr(Mcp-Session-Id)
    option httpchk GET /
    server lw1 10.0.0.11:8000 check
    server lw2 10.0.0.12:8000 check
```

Kubernetes equivalent: an `Ingress` with `nginx.ingress.kubernetes.io/affinity: cookie`
plus an explicit hash header annotation, or the `consistentHash` field
on Istio's `DestinationRule`.

## Egress hardening (audit SEC-021)

The container only needs outbound HTTPS to `cms.lobbywatch.ch:443`. In
production, enforce that with a `NetworkPolicy` (k8s) or per-container
egress rules:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: lobbywatch-mcp-egress
spec:
  podSelector:
    matchLabels: { app: lobbywatch-mcp }
  policyTypes: [Egress]
  egress:
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except: [10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.0.0/16]
      ports:
        - protocol: TCP
          port: 443
```

Combined with the existing code-layer URL allow-list in `config.py`, this
gives defence-in-depth: even if the Python URL constants are tampered
with, the runtime cannot reach private networks or the cloud-metadata IP.
