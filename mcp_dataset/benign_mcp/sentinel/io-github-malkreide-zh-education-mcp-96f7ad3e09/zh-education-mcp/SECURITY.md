# 🔒 Security Policy

[🇩🇪 Deutsche Version](SECURITY.de.md)

Thank you for helping keep `zh-education-mcp` and its users safe.

## Supported Versions

Security fixes are provided for the latest released version. Please make sure
you are running the most recent release before reporting an issue.

| Version | Supported |
|---------|-----------|
| 0.2.x   | ✅        |
| < 0.2   | ❌        |

## Reporting a Vulnerability

**Please do not open public GitHub issues for security vulnerabilities.**

Instead, report them privately:

- **Email:** hayal.oezkan@gmail.com
- Or use GitHub's [private vulnerability reporting](https://github.com/malkreide/zh-education-mcp/security/advisories/new)

Please include:

- a description of the vulnerability and its potential impact,
- steps to reproduce (proof of concept if possible),
- affected version(s) and environment.

You can expect an acknowledgement within **5 business days**. We will keep you
informed about the progress towards a fix and coordinate disclosure with you.

## Security Posture

`zh-education-mcp` is designed to minimise its attack surface:

- **Read-only:** all tools are `readOnlyHint: true` — the server cannot modify,
  delete, or write any data.
- **No authentication / no secrets:** the BISTA API is fully public; no API
  keys, tokens, or credentials are stored or transmitted.
- **No personal data:** BISTA statistics are aggregated — no individual pupil
  data is exposed or accessible.
- **Defense-in-depth:** HTTPS enforcement + host allow-list on egress, strict
  Pydantic v2 input validation, sanitised error messages, and a hardened
  container (non-root, read-only rootfs, `no-new-privileges`).

The full technical security posture, accepted risks, and network egress model
are documented in:

- [`docs/security.md`](docs/security.md) — security posture & defense-in-depth
- [`docs/network-egress.md`](docs/network-egress.md) — egress allow-list
- [`docs/secret-management.md`](docs/secret-management.md) — secret handling
- [`docs/accepted-risks.md`](docs/accepted-risks.md) — accepted risks

---

> 🇨🇭 Part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide)
