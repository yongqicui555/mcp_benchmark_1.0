# Security Policy & Posture

[🇩🇪 Deutsche Version](SECURITY.de.md)

`lobbywatch-mcp` was hardened against the internal MCP best-practice audit
catalogue. This document summarises the security posture and records the
**accepted-risk** decisions for controls that are deliberately handled at the
portfolio/gateway layer rather than inside this single server.

## Reporting a vulnerability

Please report security issues **privately** — do not open a public issue for an
exploitable vulnerability:

- Open a [GitHub Security Advisory](https://github.com/malkreide/lobbywatch-mcp/security/advisories/new), or
- Contact the maintainer ([malkreide](https://github.com/malkreide)).

You will receive an acknowledgement, and we will coordinate a fix and
disclosure timeline with you.

## Posture summary

The latest re-audit (`2026-05-09`, catalogue v1.0.0) recorded **41 pass /
0 fail / 1 partial / 2 todo** across 44 applicable checks, with
`production_ready: true` and no blocking findings. Key controls in place:

- **SSRF prevention.** A single `httpx.AsyncClient` with
  `follow_redirects=False`, an IP blocklist for RFC1918 / link-local /
  loopback / cloud-metadata ranges, and an httpx event hook that re-resolves
  the target on every request (DNS-rebinding / TOCTOU mitigation).
- **Egress allow-list.** Outbound traffic is restricted to the trusted
  Lobbywatch hosts (`cms.lobbywatch.ch` dump + `dataIF` REST) at the code
  layer, with network-layer hardening documented in `docs/deployment.md`.
- **Safe binding default.** HTTP/SSE transports bind to `127.0.0.1` by
  default; `0.0.0.0` requires explicit opt-in (NeighborJack prevention).
- **Strict input validation.** Tool arguments are typed and bounded
  (allow-listed criteria, capped `limit`, length-checked queries) at the
  Pydantic boundary.
- **No command/SQL surface.** Read-only server — no `os.system`, `shell=True`,
  `eval`, or write paths; data comes only from the JSON dump and `dataIF`.
- **Masked errors.** Upstream response bodies and stack traces are never
  forwarded to the model; structured logging goes to stderr.
- **Hardened container.** Multi-stage, non-root, read-only-rootfs-compatible
  `Dockerfile`.
- **Namespace prefix.** All tools use the `lobbywatch_` prefix to prevent
  cross-server collisions / rug-pull.
- **No secrets.** `auth_model = none` — no API keys, no secret-storage
  attack surface (Phase 1 No-Auth-First).

## Lethal Trifecta assessment (SEC-019)

Against Simon Willison's framework, this server scores roughly **1 of 3**:

1. **Access to private data** — *No.* Only public, CC BY-SA 4.0 open data.
2. **Exposure to untrusted content** — *Limited.* Reads from fixed, trusted
   Lobbywatch hosts only.
3. **Ability to exfiltrate / communicate externally** — *No.* Read-only, no
   write tools, no outbound side channel.

This makes data exfiltration through prompt injection structurally
impossible: the server cannot write, and it has no path to send data anywhere
other than back to the requesting client.

## Accepted risks (portfolio-level controls)

Two checks remain **todo** because they are deployment- or client-side
concerns, deliberately deferred to the portfolio/gateway layer rather than
duplicated inside this read-only server.

### SEC-014 — Tool allow-listing → gateway

Tool allow-listing is enforced at the deployment/gateway layer rather than
inside the server. Residual risk is low: the server is read-only, exposes
public open data, and requires no authentication.

### SEC-015 — Pre-flight tool-poisoning detection

Tool-poisoning detection is a client-side responsibility and is out of scope
for the server itself. The `lobbywatch_` namespace prefix provides
defence-in-depth against tool-name collisions.

The related **SEC-009** (session crypto-binding) is satisfied for this trust
model: the server has no concept of a user, so `Mcp-Session-Id` cannot be
bound to a `user_id`. This is acceptable for No-Auth-First read-only public
data and is documented here as the explicit trust model.

## Re-evaluation triggers

These risk acceptances must be reconsidered if the server ever:

- gains write capabilities or any side-effecting tool,
- processes personal / non-public data,
- introduces mandatory authentication or per-user sessions,
- registers tools dynamically, or
- is deployed behind a shared multi-tenant gateway.
