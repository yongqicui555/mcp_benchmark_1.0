# 🛡️ Security Policy

[🇩🇪 Deutsche Version](SECURITY.de.md)

## Supported Versions

The project is in `0.x` (alpha). Only the latest tagged release on PyPI and the
`main` branch on GitHub receive security fixes. Older `0.x` releases are not
patched.

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security findings.

Instead:

1. Open a private [GitHub Security Advisory](https://github.com/malkreide/hn-tech-signal-mcp/security/advisories/new)
   on this repository, or
2. Email the maintainer (`@malkreide`) — the address is listed on the GitHub
   profile.

Please include:

- A description of the vulnerability and the affected component.
- A reproduction case (steps, payload, or proof-of-concept code).
- The expected versus observed behaviour.
- Optionally a suggested remediation.

You will receive an acknowledgement within **7 days**. Confirmed critical or
high-severity issues are typically fixed within **14 days**; mediums and lows
are scheduled into the regular release cadence.

## Scope

In scope:

- The Python package `hn-tech-signal-mcp` (this repository).
- The MCP server itself (stdio and streamable HTTP transport).

Out of scope:

- The upstream APIs (HackerNews, Algolia, arXiv, Lobste.rs, GitHub) — report
  those to their respective operators.
- Issues that require a compromised local machine, malicious operator, or
  social-engineering.

## Audit Trail

The repository tracks past security audits under `audits/`. The current audit
baseline is `audits/2026-05-12-hn-tech-signal-mcp/`.
