# 🔒 Security Policy

🌍 **Read this in your language:** [🇩🇪 Deutsch](SECURITY.de.md)

Part of the **[Swiss Public Data MCP Portfolio](https://github.com/malkreide/swiss-public-data-mcp)**.
This document explains how to report vulnerabilities and summarises the security
posture of `swiss-electricity-mcp`.

## Supported versions

Security fixes are applied to the latest released version on PyPI. Please always
upgrade to the most recent release before reporting an issue.

| Version | Supported |
|---|---|
| Latest `0.x` | ✅ |
| Older `0.x` | ❌ |

## Reporting a vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Instead, report privately via one of:

- **GitHub Security Advisories** — use the [*Report a vulnerability*](https://github.com/malkreide/swiss-electricity-mcp/security/advisories/new)
  button under the repository's **Security** tab (preferred).
- **Email** — `hayal.oezkan@gmail.com` with the subject line
  `[SECURITY] swiss-electricity-mcp`.

Please include:

- a description of the issue and its potential impact,
- steps to reproduce (a minimal proof of concept if possible),
- affected version(s) and environment details.

**Response targets:** acknowledgement within **72 hours**, an initial assessment
within **7 days**, and a coordinated fix/disclosure timeline agreed with you.
Please give us reasonable time to release a fix before any public disclosure.

## Security posture

`swiss-electricity-mcp` is a **read-only** MCP server that exposes only public
Swiss Open Government Data. Key properties:

- **No authentication, no secrets.** All four upstreams are anonymously
  accessible public OGD endpoints — there are no API keys, tokens, or credentials
  in the code, environment, or deployment.
- **No private data, no PII.** Only public open data (CC0 / CC BY 4.0) is read.
- **Egress allow-list.** `assert_url_allowed()` gates *every* outbound request: it
  enforces HTTPS and rejects any host outside a fixed `frozenset` of four official
  hosts. Cloud-metadata IPs (`169.254.169.254`) and non-HTTPS schemes are rejected
  by construction. See [`docs/network-egress.md`](docs/network-egress.md).
- **No write or exfiltration path.** All 12 tools are read-only
  (`readOnlyHint=true`); there are no write, mail, or webhook tools.
- **Lethal-trifecta safe by construction.** At most one of {private data,
  untrusted content, exfiltration ability} is meaningfully present. See
  [`docs/security-posture.md`](docs/security-posture.md).
- **Supply-chain hygiene.** Pure-Python build via `hatchling` with no
  pre/postinstall hooks; dependencies are pinned and updated via Dependabot;
  releases publish to PyPI via an OIDC **Trusted Publisher** (no long-lived token).
  Gitleaks (`secret-scan.yml`) runs on every push/PR.

## Hardening recommendations for deployers

- In HTTP mode the host defaults to `127.0.0.1`. Only set
  `SWISS_ELECTRICITY_HOST=0.0.0.0` **inside a container**, never on a developer
  machine (NeighborJack).
- Add a network-layer egress restriction (Kubernetes `NetworkPolicy`, platform
  egress rules, or an egress proxy) as defense-in-depth.
- Never set `SWISS_ELECTRICITY_CORS_ORIGINS=*`; list explicit origins.

For the full security rationale, see [`docs/security-posture.md`](docs/security-posture.md)
and [`docs/network-egress.md`](docs/network-egress.md).
