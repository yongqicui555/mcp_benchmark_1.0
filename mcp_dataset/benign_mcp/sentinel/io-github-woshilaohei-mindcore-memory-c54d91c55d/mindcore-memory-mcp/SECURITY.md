# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.11  | :white_check_mark: |
| 0.1.10  | :white_check_mark: |
| < 0.1.10| :x:                |

## Reporting a Vulnerability

**Do not open a public issue** for security vulnerabilities.

Instead, please report security issues directly to:

- Email: **1410770089@qq.com**
- Subject: `[SECURITY] mindcore-memory-mcp — Brief description`

You will receive a response within **48 hours**. If the issue is confirmed, we will:

1. Acknowledge receipt and begin investigation
2. Develop and test a fix
3. Release a patch version
4. Publish a security advisory after the fix is deployed

## Security Features

MindCore Memory is built with production security in mind:

| Feature | Description |
|---------|-------------|
| **Input Sanitization** | All user inputs validated and sanitized before processing |
| **Path Traversal Protection** | Storage paths validated against system directory access |
| **Rate Limiting** | Token bucket rate limiter (100 req/60s) |
| **Content Encryption** | Optional Fernet encryption at rest (`MINDCORE_ENCRYPT_KEY`) |
| **Session Isolation** | Session ID validated and isolated per context |
| **Circuit Breaker** | Prevents cascade failures from compromised dependencies |
| **Error Sanitization** | Production errors stripped of internal details |
| **Bearer Token Auth** | HTTP transport supports Bearer token authentication |

## Responsible Disclosure

We appreciate responsible disclosure of security vulnerabilities. Please:

- Provide detailed steps to reproduce
- Allow reasonable time for a fix before public disclosure
- Do not access or modify user data without permission

We are happy to acknowledge researchers who follow responsible disclosure in our release notes and security advisories.
