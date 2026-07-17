# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it privately:

1. **Email**: major@mhtx.net
2. **Subject**: `[SECURITY] pcp-mcp: <brief description>`

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes (optional)

## Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 7 days
- **Fix timeline**: Depends on severity, typically within 30 days

## Security Considerations

### Authentication

pcp-mcp supports HTTP Basic authentication for pmproxy connections. Credentials are:
- Loaded from environment variables (`PCP_USERNAME`, `PCP_PASSWORD`)
- Never logged or exposed in error messages
- Transmitted securely when `PCP_USE_TLS=true`

### Host Restrictions

The `PCP_ALLOWED_HOSTS` environment variable restricts which remote hosts can be queried, preventing potential SSRF attacks when the `host` parameter is used in tools.

### TLS Configuration

- `PCP_USE_TLS`: Enable HTTPS for pmproxy connections
- `PCP_TLS_VERIFY`: Certificate verification (default: true)
- `PCP_TLS_CA_BUNDLE`: Custom CA bundle path

### Recommendations

1. **Production deployments**: Always use TLS (`PCP_USE_TLS=true`)
2. **Remote monitoring**: Configure `PCP_ALLOWED_HOSTS` to limit queryable hosts
3. **Credentials**: Use environment variables, never command-line arguments
