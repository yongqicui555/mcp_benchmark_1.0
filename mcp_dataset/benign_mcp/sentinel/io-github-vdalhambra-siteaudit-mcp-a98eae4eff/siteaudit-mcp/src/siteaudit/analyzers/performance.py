"""Performance analyzer — page size, load time, resource analysis."""

import time
from urllib.parse import urlparse
import requests


def analyze_performance(url: str, resp) -> dict:
    """Analyze page performance metrics."""
    issues = []
    warnings = []
    passed = []

    # Response time
    elapsed_ms = resp.elapsed.total_seconds() * 1000

    if elapsed_ms < 500:
        passed.append(f"Server response time: {elapsed_ms:.0f}ms (fast)")
    elif elapsed_ms < 1500:
        warnings.append(f"Server response time: {elapsed_ms:.0f}ms (could be faster)")
    else:
        issues.append(f"Slow server response: {elapsed_ms:.0f}ms (aim for <500ms)")

    # Page size
    content_length = len(resp.content)
    size_kb = content_length / 1024

    if size_kb < 100:
        passed.append(f"Page size: {size_kb:.1f}KB (lightweight)")
    elif size_kb < 500:
        passed.append(f"Page size: {size_kb:.1f}KB (acceptable)")
    elif size_kb < 1500:
        warnings.append(f"Page size: {size_kb:.1f}KB (consider optimizing)")
    else:
        issues.append(f"Large page: {size_kb:.1f}KB (aim for <500KB)")

    # Compression
    encoding = resp.headers.get("Content-Encoding", "").lower()
    if encoding in ("gzip", "br", "deflate"):
        passed.append(f"Compression enabled: {encoding}")
    else:
        warnings.append("No compression (gzip/brotli) — enable for faster loads")

    # Caching headers
    cache_control = resp.headers.get("Cache-Control", "")
    if cache_control:
        passed.append(f"Cache-Control header present: {cache_control[:60]}")
    else:
        warnings.append("No Cache-Control header — add caching for returning visitors")

    # Redirects
    redirect_count = len(resp.history)
    if redirect_count == 0:
        passed.append("No redirects")
    elif redirect_count == 1:
        passed.append(f"1 redirect ({resp.history[0].status_code})")
    else:
        warnings.append(f"{redirect_count} redirects — reduce redirect chain")

    # HTTP/2 check (from response)
    # Note: requests library doesn't directly expose HTTP version
    # but we can check for some indicators

    # Content-Type
    content_type = resp.headers.get("Content-Type", "")
    if "charset" in content_type.lower():
        passed.append("Character encoding specified in Content-Type")

    # Calculate score
    max_score = 100
    score = max_score - (len(issues) * 15) - (len(warnings) * 5)
    score = max(0, min(100, score))

    return {
        "score": score,
        "issues_count": len(issues),
        "warnings_count": len(warnings),
        "passed_count": len(passed),
        "issues": issues,
        "warnings": warnings,
        "passed": passed,
        "metrics": {
            "response_time_ms": round(elapsed_ms),
            "page_size_kb": round(size_kb, 1),
            "page_size_bytes": content_length,
            "compression": encoding or "none",
            "redirect_count": redirect_count,
            "http_status": resp.status_code,
            "content_type": content_type,
        },
    }
