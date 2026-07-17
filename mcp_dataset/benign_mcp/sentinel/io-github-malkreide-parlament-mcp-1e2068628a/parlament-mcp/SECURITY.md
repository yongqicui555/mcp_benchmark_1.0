# Security Policy & Posture

[🇩🇪 Deutsche Version](SECURITY.de.md)

`parlament-mcp` was hardened against the internal MCP best-practice audit
catalogue. This document summarises the security posture and records the
**accepted-risk** decisions for controls that are deliberately handled at the
portfolio/gateway layer rather than inside this single server.

## Reporting a vulnerability

Please open a private security advisory on the GitHub repository, or contact the
maintainer listed in `README.md`. Do not file public issues for exploitable
vulnerabilities.

## Posture summary

This is a **read-only**, **no-PII**, **public-open-data** MCP server. All 6
tools only issue OData read queries against the Curia Vista endpoint
(`ws.parlament.ch`). Hardening already in place:

| Area | Control |
|---|---|
| Egress | HTTPS-enforced allow-list to `ws.parlament.ch` only (`security.ALLOWED_HOSTS`), checked per request via `assert_host_allowed()` (SEC-021) |
| Network | Kubernetes `NetworkPolicy` permits only HTTPS/443 + DNS egress; cloud-metadata and RFC1918 ranges blocked (SEC-021) |
| Binding | Network transports default to `127.0.0.1`; `0.0.0.0` only inside a detected container, otherwise a NeighborJack warning is logged (SEC-016) |
| Transport | Streamable HTTP with CORS exposing only `Mcp-Session-Id` (SDK-004) |
| Auth | Optional, opt-in bearer tokens via `MCP_BEARER_TOKENS`; identity comes from the validated token, not a spoofable session header (SEC-009) |
| Input | Pydantic v2 strict validation at all boundaries (SEC-018) |
| Secrets | No secrets used (public API); `gitleaks` runs in CI as a regression guard; PyPI releases use OIDC trusted publishing (ARCH-005/SEC-013) |
| Errors | Human-readable German error strings; upstream bodies logged to stderr, never forwarded to the model (OBS-002) |
| Stdout | Reserved for the JSON-RPC stream; structured logging pinned to stderr (OBS-004) |
| Tool allow-list | Server-side, default-deny allow-list via `gateway.filter_allowed_tools()` (SEC-014) |
| Tool integrity | SHA-256 tool-hash pinning verified in CI against `tool-hashes.json` (SEC-022) |

See [`docs/security.md`](docs/security.md) for the full security write-up
(Lethal-Trifecta assessment, egress allow-list, gateway hardening), `audits/`
for the audit reports, and [`CHANGELOG.md`](CHANGELOG.md) for the hardening
history.

## Lethal Trifecta assessment (SEC-019)

A server becomes dangerous only when it combines **all three** of Simon
Willison's "lethal trifecta" capabilities:

| Capability | Status | Rationale |
|---|:--:|---|
| Access to private data | ❌ No | Public open data only (Curia Vista). No PII, no internal administrative data. |
| Exposure to untrusted content | ⚠️ Limited | Reads only the fixed, trusted Curia Vista API; no user uploads, no arbitrary web scraping. |
| External communication / write | ❌ No | Read-only; all tools `readOnlyHint: true`. No mail/webhook/POST capability. |

**Trifecta score: ~1 of 3 → safe.** Data exfiltration via prompt injection is
structurally impossible: the server neither reads private data nor sends data
outbound.

## Accepted risks (portfolio-level controls)

The following audit checks are **not** fully implemented inside this server by
design. They are portfolio-wide concerns best enforced at an MCP gateway / host
layer, and the residual risk here is low because the server is read-only and
only reaches a single trusted public-data provider.

### SEC-009 — Session crypto-binding → optional (no mandatory auth)

**Status:** optional in Phase 1. `parlament-mcp` exposes public open data with no
mandatory authentication, so there is no user identity to bind a session to by
default. The repo already ships `auth.SessionSigner` (HMAC-SHA256, TTL,
revocation, user-binding) for deployments that enable bearer auth; binding
becomes mandatory in Phase 3 (write) — see [`docs/roadmap.md`](docs/roadmap.md).

### SEC-015 — Pre-flight tool-poisoning detection

**Status:** accepted risk (portfolio-level) — with a local guard in place.
Tool-poisoning (malicious tool descriptions / rug-pulls) is a supply-chain and
host-side concern. This server's tool definitions are version-controlled,
authored in-repo, and reviewed via PR; there is no dynamic/remote tool
registration. Locally, **SEC-022 tool-hash pinning** (`tool-hashes.json`)
detects any drift in the tool surface in CI, and `gateway.scan_tool_definition()`
provides reusable poisoning detection for the multi-server case. Cross-server
poisoning detection remains a gateway/host responsibility tracked at the
portfolio level.

## Re-evaluation triggers

These acceptances should be revisited if the server ever:

- gains **write** capability or starts processing **PII**, or
- adds a **mandatory authentication** model (then enforce SEC-009: bound, TTL'd,
  server-side-invalidated session IDs and re-audit before merge), or
- registers tools **dynamically** / from remote sources, or
- is aggregated behind a shared MCP gateway (then enable the gateway's tool
  allow-listing and tool-poisoning detection).
