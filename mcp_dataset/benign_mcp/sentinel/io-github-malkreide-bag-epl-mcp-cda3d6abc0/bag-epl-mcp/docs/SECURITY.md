# Security Model — `bag-epl-mcp`

This document records the threat model and the deliberate security design
decisions for the BAG ePL MCP server. It is referenced by the
[mcp-audit-skill](https://github.com/malkreide/mcp-audit-skill) audit
(`docs/audit/2026-06-01/`) and addresses checks SEC-019, SEC-009, SEC-014,
SEC-015, SEC-004/005/021 and SEC-016.

## 1. Capability profile

| Property | Value |
|----------|-------|
| Authentication | **none** (public data, no API key) |
| Data class | **Public Open Data** (BAG SL / GGSL / MiGeL, Fedlex) |
| Write capability | **none** — all tools perform HTTP `GET` only |
| Filesystem / shell access | none |
| Sampling / sequential thinking | none |
| External requests | only to a fixed allow-list of `*.admin.ch` hosts |

Because there is **no authentication, no PII, and no write path**, the entire
classes of OAuth, PII/DSG, HITL, idempotency and DLP controls are
out-of-scope by design (24 of 68 audit checks are not applicable).

## 2. Lethal Trifecta assessment (SEC-019)

The "lethal trifecta" is dangerous only when a single server combines all
three of: **(A)** access to private data, **(B)** exposure to untrusted
content, **(C)** the ability to communicate externally.

| Capability | Present? | Notes |
|------------|:---:|-------|
| A — private data | **No** | only public regulatory lists are read |
| B — untrusted content | Partial | tool arguments come from the LLM/user |
| C — external comms | **Yes** (read-only) | `GET` to fixed BAG/Fedlex hosts |

**Score: 2 / 3** (B + C), and C is read-only against a hard-coded allow-list.
There is no private data to exfiltrate and no write/send channel, so the
prompt-injection → exfiltration chain does not close. No Architecture Decision
Record beyond this section is required.

## 3. Session & authentication model (SEC-009)

The server is **stateless and unauthenticated**: there is no user identity and
no per-user state. Over Streamable HTTP, session handling is delegated to the
MCP SDK's default session manager; the server adds no custom `user_id:session_id`
binding because there is no user identity to bind and no confidential per-session
data to protect.

**Operational requirement:** run Phase 1 as a **single instance**. When scaling
horizontally, sticky-session load balancing keyed on the `Mcp-Session-Id` header
is required so stateful Streamable-HTTP sessions stay on one backend
(SCALE-002/003) — a reference HAProxy stick-table config with an explicit
session TTL is provided in [`../deploy/haproxy.cfg`](../deploy/haproxy.cfg).
Introducing authentication or per-user state in a later phase **must**
re-introduce signed session binding and trigger a re-audit.

## 4. Egress controls (SEC-004 / SEC-005 / SEC-021)

The fast pre-check `_assert_safe_url()` runs before any outbound call (HTTPS-only
+ host allow-list). The actual connection is made through a **DNS-pinned**
transport (`_PinnedNetworkBackend`) so the hostname is resolved **exactly once**,
the resolved IP is validated and the TCP connection is pinned to it, while TLS
SNI and certificate verification still use the original hostname (SEC-005,
eliminates the resolve/connect TOCTOU). Concretely:

- **HTTPS only** — non-`https` schemes are rejected.
- **Code-layer allow-list** — the host must be in the immutable
  `ALLOWED_HOSTS` frozenset (`sl.bag.admin.ch`, `www.bag.admin.ch`,
  `www.fedlex.admin.ch`). Default-deny.
- **Single-resolution + pinned IP** — `_resolve_and_validate()` rejects private,
  loopback, link-local and reserved IPs (blocks SSRF pivots and the cloud
  metadata endpoint `169.254.169.254`) and returns the pinned address.

**Defense-in-depth (deployment):** add a network-layer egress policy
(e.g. Render egress rules / Kubernetes `NetworkPolicy`) restricting outbound
traffic to the same hosts. To extend the allow-list, edit `ALLOWED_HOSTS` and
the network policy together, and note it in the `CHANGELOG`.

## 5. Network exposure (SEC-016)

- Default transport is **stdio**, which opens **no** network ports.
- Host binding is controlled by `MCP_HOST` and defaults to `127.0.0.1`.
- `MCP_HOST=0.0.0.0` must be set **only** inside a container / cloud
  environment that fronts the service — never on a shared local machine.

### Container hardening (SEC-007 / SCALE-004 / SCALE-006)

The provided multi-stage `Dockerfile` runs the service as a **non-root** user
(UID 10001) from a slim base image and declares a `HEALTHCHECK` against
`/healthz`. The `render.yaml` Blueprint pins a resource `plan` (memory/CPU
limit) and wires the health check. When running the image directly, also apply
runtime limits, e.g.:

```bash
docker run --read-only --cap-drop ALL \
  --memory 256m --cpus 0.5 --ulimit nofile=4096:4096 \
  -e MCP_TRANSPORT=streamable-http -e MCP_HOST=0.0.0.0 -p 8000:8000 \
  bag-epl-mcp
```

## 6. Gateway / tool governance (SEC-014 / SEC-015)

The server publishes a small, fixed set of **six read-only** tools, all
namespaced with the `epl_` prefix and annotated `readOnlyHint=true`. An
enterprise MCP gateway with per-team tool allow-listing and pre-flight
tool-poisoning detection is **not** deployed: there is no enterprise / Stadt
Zürich context, the tool surface is static and read-only, and no sensitive
data flows through it. If this server is ever placed behind a central gateway,
configure a default-deny allow-list for the `epl_*` tools there.

## 7. Reporting

Security issues: please open a private report via
[GitHub Security Advisories](https://github.com/malkreide/bag-epl-mcp/security/advisories)
or the repository issues, without including any sensitive data.
