# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in SiteAudit MCP, please report it responsibly:

1. **Do NOT open a public GitHub issue** for security vulnerabilities
2. Email **victor@siteaudit.dev** with details of the vulnerability
3. Include steps to reproduce, impact assessment, and any suggested fixes

We will acknowledge your report within 48 hours and provide a timeline for resolution.

## Security Design

SiteAudit MCP is designed with security in mind:

- **No credentials stored**: The server uses only free, public APIs
- **No database**: All audit results are computed in real-time, never stored
- **No user data collection**: The server does not store, log, or transmit any user data
- **Read-only operations**: All tools perform read-only analysis; no modifications to target sites
- **Minimal dependencies**: Only well-maintained, widely-used Python packages
- **No file system access**: The server does not read or write files on the host system

## External API Calls

This server makes outgoing HTTP requests **only** to:

| API | Purpose | Auth Required |
|-----|---------|--------------|
| Target URL (user-provided) | Fetch HTML for SEO/security/performance analysis | No |
| Google PageSpeed Insights | Lighthouse performance metrics | No (free API) |

No other network connections are made. All HTML parsing and analysis is performed locally using BeautifulSoup and Python's built-in `ssl` module.
