# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in StockSense, please report it responsibly:

1. **Do not** open a public GitHub issue.
2. Email **security@stocksense.dev** with a description of the vulnerability.
3. Include steps to reproduce, if possible.

We will acknowledge your report within 48 hours and aim to release a fix within 7 days for critical issues.

## Scope

StockSense fetches data from public APIs (SEC EDGAR, Yahoo Finance). It does not store credentials, manage user accounts, or process payments. The primary security concerns are:

- **Dependency vulnerabilities** — We run `pip-audit` in CI on every PR.
- **Input validation** — All ticker symbols and parameters are validated before use.
- **No secrets in artifacts** — Build artifacts are inspected before each release.
