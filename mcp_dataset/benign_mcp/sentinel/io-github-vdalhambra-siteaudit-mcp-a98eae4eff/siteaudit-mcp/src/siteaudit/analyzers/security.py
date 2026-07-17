"""Security analyzer — HTTPS, headers, cookies, SSL certificate check."""

import ssl
import socket
import datetime
from urllib.parse import urlparse


def analyze_security(url: str, resp) -> dict:
    """Analyze security headers and SSL configuration."""
    issues = []
    warnings = []
    passed = []
    headers = {k.lower(): v for k, v in resp.headers.items()}

    # HTTPS check
    if resp.url.startswith("https://"):
        passed.append("Site uses HTTPS")
    else:
        issues.append("Site does NOT use HTTPS — critical security issue")

    # Strict-Transport-Security (HSTS)
    hsts = headers.get("strict-transport-security")
    if hsts:
        passed.append(f"HSTS header present: {hsts[:80]}")
        if "includesubdomains" in hsts.lower():
            passed.append("HSTS includes subdomains")
        if "preload" in hsts.lower():
            passed.append("HSTS preload enabled")
    else:
        issues.append("Missing Strict-Transport-Security (HSTS) header")

    # Content-Security-Policy
    csp = headers.get("content-security-policy")
    if csp:
        passed.append("Content-Security-Policy header present")
    else:
        warnings.append("Missing Content-Security-Policy (CSP) header")

    # X-Content-Type-Options
    xcto = headers.get("x-content-type-options")
    if xcto and "nosniff" in xcto.lower():
        passed.append("X-Content-Type-Options: nosniff")
    else:
        warnings.append("Missing X-Content-Type-Options: nosniff header")

    # X-Frame-Options
    xfo = headers.get("x-frame-options")
    if xfo:
        passed.append(f"X-Frame-Options: {xfo}")
    else:
        warnings.append("Missing X-Frame-Options header (clickjacking protection)")

    # Referrer-Policy
    rp = headers.get("referrer-policy")
    if rp:
        passed.append(f"Referrer-Policy: {rp}")
    else:
        warnings.append("Missing Referrer-Policy header")

    # Permissions-Policy (formerly Feature-Policy)
    pp = headers.get("permissions-policy") or headers.get("feature-policy")
    if pp:
        passed.append("Permissions-Policy header present")
    else:
        warnings.append("Missing Permissions-Policy header")

    # X-XSS-Protection (legacy but still checked)
    xss = headers.get("x-xss-protection")
    if xss:
        passed.append(f"X-XSS-Protection: {xss}")

    # Server header disclosure
    server = headers.get("server")
    if server:
        warnings.append(f"Server header discloses: '{server}' — consider removing")

    # X-Powered-By disclosure
    powered = headers.get("x-powered-by")
    if powered:
        warnings.append(f"X-Powered-By header discloses: '{powered}' — remove it")

    # Cookie security (check Set-Cookie headers)
    cookies = resp.headers.get("Set-Cookie", "")
    if cookies:
        if "secure" not in cookies.lower():
            warnings.append("Cookies missing Secure flag")
        if "httponly" not in cookies.lower():
            warnings.append("Cookies missing HttpOnly flag")
        if "samesite" not in cookies.lower():
            warnings.append("Cookies missing SameSite attribute")

    # SSL Certificate check
    ssl_info = _check_ssl_cert(url)

    # Calculate score — issues are critical, warnings are minor
    max_score = 100
    score = max_score - (len(issues) * 15) - (len(warnings) * 3)
    score = max(0, min(100, score))

    return {
        "score": score,
        "issues_count": len(issues),
        "warnings_count": len(warnings),
        "passed_count": len(passed),
        "issues": issues,
        "warnings": warnings,
        "passed": passed,
        "ssl_certificate": ssl_info,
        "headers_present": {
            "hsts": bool(hsts),
            "csp": bool(csp),
            "x_content_type_options": bool(xcto),
            "x_frame_options": bool(xfo),
            "referrer_policy": bool(rp),
            "permissions_policy": bool(pp),
        },
    }


def _check_ssl_cert(url: str) -> dict | None:
    """Check SSL certificate details."""
    parsed = urlparse(url if url.startswith("http") else f"https://{url}")
    hostname = parsed.netloc or parsed.path.split("/")[0]
    hostname = hostname.split(":")[0]

    try:
        context = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        with socket.create_connection((hostname, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                protocol = ssock.version()

        # Parse expiry
        not_after = cert.get("notAfter", "")
        not_before = cert.get("notBefore", "")
        issuer_parts = cert.get("issuer", ())
        issuer = ""
        for rdn in issuer_parts:
            for attr in rdn:
                if attr[0] == "organizationName":
                    issuer = attr[1]

        # Parse dates
        try:
            expiry = datetime.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
            days_left = (expiry - datetime.datetime.utcnow()).days
        except (ValueError, TypeError):
            expiry = None
            days_left = None

        # Subject Alternative Names
        san = []
        for type_val in cert.get("subjectAltName", ()):
            if type_val[0] == "DNS":
                san.append(type_val[1])

        return {
            "valid": True,
            "issuer": issuer,
            "protocol": protocol,
            "expires": not_after,
            "days_until_expiry": days_left,
            "expiry_warning": days_left is not None and days_left < 30,
            "subject_alt_names": san[:5],
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}
