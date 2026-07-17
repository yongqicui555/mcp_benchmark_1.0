# Security Policy

[🇩🇪 Deutsche Version](SECURITY.de.md)

This document describes the security model of **bakom-mcp** and how to report a vulnerability responsibly. The server is part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide).

---

## Supported Versions

Security fixes are provided for the latest released minor version. Older versions are not maintained — please upgrade before reporting.

| Version | Supported          |
|---------|--------------------|
| 2.x     | ✅ Yes             |
| < 2.0   | ❌ No              |

---

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Report privately through GitHub's [private vulnerability reporting](https://github.com/malkreide/bakom-mcp/security/advisories/new) (**Security → Report a vulnerability**). This keeps the details confidential until a fix is available.

Please include:

- A description of the vulnerability and its potential impact
- Steps to reproduce (proof of concept, affected tool, input values)
- The affected version (`bakom-mcp --version` or `pip show bakom-mcp`)
- Any suggested mitigation, if known

**Response targets:**

- **Acknowledgement:** within 72 hours
- **Initial assessment:** within 7 days
- **Fix / coordinated disclosure:** depending on severity, typically within 30 days

Please allow a reasonable period for a fix before any public disclosure. Reporters who follow this process will be credited in the release notes unless they prefer to remain anonymous.

---

## Security Model

**bakom-mcp** is designed with a minimal attack surface. By design the server:

- ✅ Is **read-only** (`readOnlyHint: true`) — it has no write, delete, or mutation tools.
- ✅ Requires **no authentication tokens or secrets** — all data sources are public Open Government Data (OGD).
- ✅ Restricts outbound traffic to a code-layer **egress allow-list** of the known BAKOM/Confederation data-source hosts ([`src/bakom_mcp/server.py`](src/bakom_mcp/server.py)).
- ✅ Validates all coordinate inputs against the **Swiss WGS84 bounding box** (lat 45.8–47.9, lon 5.9–10.6) via Pydantic.
- ✅ Does **not** access the local filesystem (no path-traversal surface).
- ✅ Does **not** execute shell commands or arbitrary code (no `subprocess` / `os.system` / `eval`).
- ✅ Does **not** cache or persist user inputs across calls.
- ✅ Enforces per-query limits (max 50 antennas, max 20 locations, max 50 RTV results) and a 20-second timeout per upstream call.

### HTTP / Cloud Deployment

When run with the HTTP transport (`--http`):

- The server binds to `127.0.0.1` by default; binding to `0.0.0.0` logs a warning and should only be done on trusted networks.
- CORS is **disabled** unless `BAKOM_MCP_CORS_ORIGINS` is explicitly configured.
- For public exposure, terminate TLS and CORS at a reverse proxy (Caddy, Traefik, nginx).

### Container Hardening

The provided Docker image runs as **non-root** (UID 10001), uses a **read-only filesystem**, drops **all Linux capabilities**, refuses **privilege escalation** (`no-new-privileges`), and applies memory/CPU/PID limits (see [`docker-compose.yml`](docker-compose.yml)).

### Supply Chain

- Dependencies are version-pinned with upper bounds in [`pyproject.toml`](pyproject.toml).
- A [secret-scanning workflow](.github/workflows/secret-scan.yml) runs in CI to prevent accidental credential commits.
- Independent security audit reports are published under [`audits/`](audits/).

---

## Scope

In scope:

- The `bakom-mcp` server code in this repository
- Input validation, egress controls, and the HTTP transport configuration

Out of scope:

- Vulnerabilities in upstream data providers (geo.admin.ch, opendata.swiss, rtvdb.ofcomnet.ch) — report those to the respective operators
- The accuracy or availability of the open data itself
- General network/DoS issues against third-party public APIs

---

*Thank you for helping keep bakom-mcp and the Swiss Public Data MCP Portfolio secure.*
