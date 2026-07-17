# Security Posture

This document records the security controls implemented in `swiss-cultural-heritage-mcp` and the recommended deployment hardening for downstream operators. It maps to the [2026-05-21 audit](../audits/2026-05-21-swiss-cultural-heritage-mcp/report.md).

## Threat model

The server is **read-only** and **anonymous**:

- No authentication surface (all upstream APIs are public open data)
- No write operations (all tools annotated `readOnlyHint: true`)
- No PII processed — only institutional records (artists, museum objects, publications)
- No persistent state (stateless; no database, no cache)

Residual risks the controls below mitigate:
- Server-side request forgery (SSRF) via redirect chains or future user-supplied URLs
- XML attacks (entity expansion / billion laughs) against OAI-PMH responses
- Local-filesystem escalation from a compromised process
- Cross-border data flow non-compliance (revDSG / EDÖB) — see [`data-residency.md`](data-residency.md)

## Controls in code

| Control | Location | Audit ref |
|---|---|---|
| Egress allow-list (`frozenset` of two upstreams) | `server.py:_assert_allowed` | SEC-021 |
| HTTPS-only scheme enforcement (rejects `http://`/`file://` even for an allow-listed host) | `server.py:_assert_allowed` | SEC-004 |
| Manual redirect following with a per-hop allow-list re-check (client keeps `follow_redirects=False`) | `server.py:_http_get` | SEC-021 |
| `defusedxml.ElementTree` for OAI-PMH parsing | `server.py` imports | SEC (XML) |
| Pydantic input models with `extra="forbid"`, length caps, regex date patterns | every `*Input` class | input validation |
| Narrow `except ExpectedUpstreamError` (httpx + XML + ValueError); handled failures raised as `ToolError` so the client receives an `isError: true` result, not a plain string | every tool body / `server.py:_raise_tool_error` | OBS-001 |
| Unexpected (programming) errors masked: full detail to stderr, generic `ToolError` to the client | `server.py:mask_unexpected_errors` | OBS-002 |
| Shared httpx client owned by FastMCP `lifespan` | `server.py:lifespan` | SDK-001 |
| CORS exposes `Mcp-Session-Id` with an explicit (non-wildcard) origin allow-list | `server.py:build_http_app` | SDK-004 |
| HTTP host defaults to `127.0.0.1`; only the container sets `MCP_HOST=0.0.0.0` | `server.py` entry point / `Dockerfile` | SEC-016 |

See [`network-egress.md`](network-egress.md) for the allow-list contents and the update procedure.

## SSRF & DNS rebinding (SEC-004 / SEC-005)

The primary SSRF control is the **two-host egress allow-list**, re-checked on every redirect hop, combined with the fact that **no tool input controls the request host** — only query strings and CKAN `resource_id`s are user-supplied; every base URL is a module constant. A redirect to a metadata IP (e.g. `169.254.169.254`) is rejected because it is not in `ALLOWED_HOSTS`, and (since SEC-004) a scheme downgrade to `http://` or a `file://` URL is rejected even for an allow-listed host.

The following are **defense-in-depth measures deliberately deferred** while the allow-list holds exactly two trusted Swiss-federal hosts. They carry low real-world risk today; the table records the trigger that would make them required.

| Measure | Audit ref | Status | Trigger to implement |
|---|---|---|---|
| Resolved-IP blocklist for private / link-local / loopback ranges (incl. `169.254.169.254`, IPv6 `::1`, `fe80::/10`) before connecting | SEC-004 | Deferred | Any tool starts accepting a user-supplied URL/host, **or** the allow-list grows beyond trusted fixed hosts. |
| DNS pinning — resolve the host once, pin the resolved IP for the TCP connection, keep the original hostname for SNI / `Host` / certificate validation (closes the TOCTOU window) | SEC-005 | Deferred | Same trigger as above; an attacker would otherwise need to control DNS for `ckan.opendata.swiss` or `helveticat.nb.admin.ch`. |

**Why deferred:** with a closed two-host allow-list and no user-controlled host, the resolved-IP and DNS-rebinding vectors are not reachable in practice. Implementing them (a custom `httpx` transport/resolver) before they are reachable adds complexity and a maintenance surface for no live risk reduction. If either trigger above occurs, implement **both** before shipping the change, and add the corresponding `_assert_allowed` / transport tests.

## Tool-definition pinning & namespacing (SEC-022)

To guard against a **"rug pull"** — a silently changed tool name or prompt that
re-tasks the LLM — the repository commits a hash snapshot of every tool's
`name` + cleaned docstring (the LLM-facing `description`) at
[`audits/tool-pins/current.json`](../audits/tool-pins/current.json). A CI test
(`TestToolPins`) recomputes the live hashes on every run and fails on any drift,
forcing a conscious regeneration (`scripts/pin_tools.py`) plus a CHANGELOG
**re-approval** note when a tool definition changes. The pin deliberately
excludes the pydantic/SDK-generated JSON schema (whose serialised form varies
across dependency versions, which would cause false positives); the schema/IO
contract is covered by the structured-output and input-validation tests. See
[`audits/tool-pins/README.md`](../audits/tool-pins/README.md) for the process.

**Deferred (breaking):** SEC-022 also suggests a `<server>__<tool>` server-identity
prefix instead of the current consistent `heritage_` prefix. Renaming every tool
id is a breaking change for existing client configurations (a major version
bump), so it is deferred as a Phase-2 decision. The hash pin above provides the
drift-detection benefit without the breakage; the `heritage_` prefix remains
consistent and is namespaced under the server in practice via the MCP client.

## Horizontal scaling (SCALE-002 / SCALE-003)

The deployment is **single-instance by constraint**. The Streamable-HTTP transport keeps a per-session state (`Mcp-Session-Id`) in process, so scaling to more than one instance requires session affinity or a shared session backend first. The full constraint, session model, and the path to safe horizontal scaling are documented in [`scaling.md`](scaling.md).

## Lethal Trifecta assessment (SEC-019)

The "lethal trifecta" is the combination of (1) access to **private** data, (2) exposure to **untrusted** content, and (3) the ability to **exfiltrate** (write/send externally). A server should hold at most two of the three.

| Leg | Present? | Rationale |
|---|---|---|
| Private-data access | **No** | Only public open data (opendata.swiss CKAN, NB OAI-PMH). No auth, no PII, no internal systems. |
| Untrusted-content exposure | Partial | Upstream responses are rendered for the LLM. The upstreams are Swiss federal services, but their content is still treated as data, not instructions. |
| Exfiltration channel | **No** | Read-only: no write/send/mail/webhook tools. Outbound traffic is restricted to the two-host egress allow-list (`SEC-021`), declared as an immutable `frozenset`. |

**Conclusion:** the server holds **at most one** leg of the trifecta, so the trifecta is **not present**. This assessment must be re-run if any tool gains a write/send side effect (see the Phase 1 → 2 gate in [`roadmap.md`](roadmap.md)).

## Secret management (SEC-013)

The server handles **no secrets**: no API keys, tokens, or credentials (all upstreams are anonymous public APIs). This corresponds to Level 1 (no secret material) — acceptable for the `Public Open Data` data class. If a future upstream requires a key, store it in a Secret Manager (Switzerland/EU region per [`data-residency.md`](data-residency.md)), load it as a Pydantic `SecretStr`, keep it out of logs, and never bake it into the container image layer.

## Resource limits (SCALE-006)

The container declares no limits itself; operators should set them at the platform level. Recommended starting points for this lightweight, stateless server:

| Resource | Request | Limit |
|---|---|---|
| CPU | `100m` | `500m` |
| Memory | `128Mi` | `256Mi` |
| File descriptors (`ulimit -n`) | — | `≥ 4096` (the cross-search tool opens several concurrent upstream connections) |

Set an explicit restart policy (`restartPolicy: Always` on k8s; Render restarts on crash by default) so an OOM or upstream-induced crash recovers cleanly. Requests are deliberately below limits to allow short bursts during `heritage_cross_search` fan-out.

## Container hardening (operators)

A reference `Dockerfile` is shipped at the repo root. Key properties:

- Multi-stage build: dependencies are installed in a `builder` stage and copied into the runtime stage, so no pip cache or build tooling ships in the final image (`SCALE-004`)
- Non-root user, UID `10001`
- Slim Python base image
- `EXPOSE 8000` for Streamable HTTP mode
- `HEALTHCHECK` probing the in-app `/health` route (`SCALE-004`)
- `MCP_HOST=0.0.0.0` set only in the image so the container is reachable behind the LB while the code default stays loopback (`SEC-016`)

When deploying to a Kubernetes-class platform (k8s, Cloud Run, Fly.io, Knative) apply the following `SecurityContext`:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 10001
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
  seccompProfile:
    type: RuntimeDefault
```

For Render.com, Railway, Fly.io: confirm the platform's default sandbox includes seccomp + non-root. None of those platforms grant containers raw socket / `CAP_NET_RAW` access by default.

## stdio mode (Claude Desktop / `uvx`)

When the server runs locally as a stdio child of Claude Desktop, it inherits the user's process privileges. There is no container boundary in this mode. Mitigations:

- The egress allow-list still applies — the server cannot reach hosts other than the three upstreams even if a tool description were poisoned.
- No filesystem-writing tools are exposed.
- No subprocess / shell execution.

If you run this server alongside other MCP servers that *do* touch the filesystem or run subprocesses, sandbox the whole Claude Desktop process accordingly.

## Reporting issues

Open a private security advisory on the repository, or contact the maintainer directly. Do not file public issues for credential leaks or unpatched vulnerabilities.
