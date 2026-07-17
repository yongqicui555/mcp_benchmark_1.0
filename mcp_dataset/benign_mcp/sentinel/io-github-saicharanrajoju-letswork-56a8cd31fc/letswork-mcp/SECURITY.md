# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 3.x.x   | Yes       |
| < 3.0   | No        |

## Threat Model

LetsWork is designed for two trusted developers collaborating over a temporary session. The security model assumes:

- The **host** is fully trusted and controls the project directory
- The **guest** is a known collaborator whose file writes require host approval
- Sessions are ephemeral — tokens are generated fresh each run and not persisted

## Security Features

- **Token authentication** — cryptographically secure tokens via `secrets.token_urlsafe(32)`, validated with `hmac.compare_digest()` (constant-time, no timing attacks)
- **Path traversal prevention** — all file paths resolved and validated against the project root before any operation
- **Approval queue** — guest file writes are held for host review before being written to disk
- **File size limit** — 1MB cap on reads and writes
- **Text-only enforcement** — binary files are rejected
- **Lock ownership** — only the lock holder can release their own lock; host can force-unlock
- **Cloudflare tunnel** — session URL is HTTPS, not exposed on a raw port

## Scope & Limitations

- LetsWork is **not** designed for untrusted guests. Only share your guest token with someone you trust.
- The approval queue is in-memory — a host process crash will lose pending guest submissions (git is the safety net).
- No persistent storage of tokens or sessions between runs.

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not open a public issue**.

Report it privately via GitHub's security advisory feature:  
**[Report a vulnerability](https://github.com/saicharanrajoju/LetsWork/security/advisories/new)**

Include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact

You can expect an acknowledgement within 48 hours.
