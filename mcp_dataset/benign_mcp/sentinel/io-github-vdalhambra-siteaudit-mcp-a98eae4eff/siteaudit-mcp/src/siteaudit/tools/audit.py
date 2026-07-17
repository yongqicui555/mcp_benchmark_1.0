"""Audit tools — the main tools exposed via MCP."""

import time
from typing import Annotated
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from pydantic import Field
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from siteaudit.utils.fetcher import fetch_page, fetch_url, get_domain, SESSION, _normalize_url
from siteaudit.analyzers.seo import analyze_seo
from siteaudit.analyzers.security import analyze_security
from siteaudit.analyzers.pagespeed import analyze_pagespeed
from siteaudit.analyzers.performance import analyze_performance

# Cache for link check results (5 min TTL)
_link_check_cache: dict[str, tuple[dict, float]] = {}
_LINK_CACHE_TTL = 300


def register_audit_tools(mcp: FastMCP) -> None:
    """Register audit tools on the MCP server."""

    @mcp.tool(
        tags={"audit", "comprehensive"},
        annotations={"readOnlyHint": True},
    )
    def full_audit(
        url: Annotated[str, Field(description="URL to audit (e.g., 'example.com' or 'https://example.com')")],
    ) -> dict:
        """Run a comprehensive audit on a URL — SEO, performance, and security in one call.

        Returns a unified score (0-100) plus detailed results for each category.
        This is the most complete analysis available.
        """
        resp, soup = fetch_page(url)
        actual_url = resp.url

        seo = analyze_seo(actual_url, resp, soup)
        perf = analyze_performance(actual_url, resp)
        sec = analyze_security(actual_url, resp)

        # Overall score (weighted average)
        overall = round(seo["score"] * 0.4 + perf["score"] * 0.3 + sec["score"] * 0.3)

        # Collect top issues across all categories
        all_issues = (
            [f"[SEO] {i}" for i in seo["issues"]]
            + [f"[Performance] {i}" for i in perf["issues"]]
            + [f"[Security] {i}" for i in sec["issues"]]
        )
        all_warnings = (
            [f"[SEO] {w}" for w in seo["warnings"][:5]]
            + [f"[Performance] {w}" for w in perf["warnings"][:3]]
            + [f"[Security] {w}" for w in sec["warnings"][:5]]
        )

        grade = _score_to_grade(overall)

        return {
            "url": actual_url,
            "overall_score": overall,
            "grade": grade,
            "scores": {
                "seo": seo["score"],
                "performance": perf["score"],
                "security": sec["score"],
            },
            "top_issues": all_issues,
            "top_warnings": all_warnings[:10],
            "seo": seo,
            "performance": perf,
            "security": sec,
        }

    @mcp.tool(
        tags={"audit", "seo"},
        annotations={"readOnlyHint": True},
    )
    def seo_audit(
        url: Annotated[str, Field(description="URL to analyze for SEO")],
    ) -> dict:
        """Run an SEO-focused audit on a URL.

        Checks title tags, meta descriptions, headings, images alt text,
        internal/external links, canonical URLs, Open Graph, structured data,
        mobile viewport, and content length. Returns score + actionable recommendations.
        """
        resp, soup = fetch_page(url)
        result = analyze_seo(resp.url, resp, soup)
        result["url"] = resp.url
        return result

    @mcp.tool(
        tags={"audit", "security"},
        annotations={"readOnlyHint": True},
    )
    def security_audit(
        url: Annotated[str, Field(description="URL to check for security")],
    ) -> dict:
        """Run a security audit on a URL.

        Checks HTTPS, HSTS, CSP, X-Frame-Options, cookie flags,
        SSL certificate validity and expiration, server disclosure,
        and other security headers. Returns score + fixes needed.
        """
        resp, soup = fetch_page(url)
        result = analyze_security(resp.url, resp)
        result["url"] = resp.url
        return result

    @mcp.tool(
        tags={"audit", "performance"},
        annotations={"readOnlyHint": True},
    )
    def performance_audit(
        url: Annotated[str, Field(description="URL to check for performance")],
    ) -> dict:
        """Check page performance — response time, page size, compression, caching.

        Returns server response time, page size, compression status,
        redirect chain analysis, and caching header review.
        """
        resp, soup = fetch_page(url)
        result = analyze_performance(resp.url, resp)
        result["url"] = resp.url
        return result

    @mcp.tool(
        tags={"audit", "comparison"},
        annotations={"readOnlyHint": True},
    )
    def compare_sites(
        urls: Annotated[str, Field(description="Comma-separated URLs to compare (e.g., 'example.com,competitor.com')")],
    ) -> dict:
        """Compare SEO and performance scores of multiple websites side by side.

        Useful for competitive analysis — see how your site stacks up
        against competitors across SEO, performance, and security.
        """
        url_list = [u.strip() for u in urls.split(",") if u.strip()]
        if len(url_list) < 2:
            raise ToolError("Provide at least 2 URLs to compare, separated by commas.")
        if len(url_list) > 5:
            url_list = url_list[:5]

        results = []
        for u in url_list:
            try:
                resp, soup = fetch_page(u)
                seo = analyze_seo(resp.url, resp, soup)
                perf = analyze_performance(resp.url, resp)
                sec = analyze_security(resp.url, resp)
                overall = round(seo["score"] * 0.4 + perf["score"] * 0.3 + sec["score"] * 0.3)

                results.append({
                    "url": resp.url,
                    "overall_score": overall,
                    "grade": _score_to_grade(overall),
                    "seo_score": seo["score"],
                    "performance_score": perf["score"],
                    "security_score": sec["score"],
                    "issues_count": seo["issues_count"] + perf["issues_count"] + sec["issues_count"],
                    "page_size_kb": perf["metrics"]["page_size_kb"],
                    "response_time_ms": perf["metrics"]["response_time_ms"],
                })
            except Exception as e:
                results.append({"url": u, "error": str(e)})

        # Rank by overall score
        valid = [r for r in results if "overall_score" in r]
        ranked = sorted(valid, key=lambda x: x["overall_score"], reverse=True)
        for i, r in enumerate(ranked):
            r["rank"] = i + 1

        best = ranked[0]["url"] if ranked else None
        return {
            "sites_compared": len(url_list),
            "best_overall": best,
            "comparison": results,
        }

    @mcp.tool(
        tags={"audit", "performance", "lighthouse"},
        annotations={"readOnlyHint": True},
    )
    def lighthouse_audit(
        url: Annotated[str, Field(description="URL to audit with Google Lighthouse")],
        strategy: Annotated[str, Field(description="'mobile' or 'desktop' (default: mobile)")] = "mobile",
    ) -> dict:
        """Run Google Lighthouse via PageSpeed Insights API — get performance, accessibility, SEO, and best-practices scores plus Core Web Vitals (LCP, INP, CLS).

        Returns Lighthouse scores (0-100), Core Web Vitals with ratings,
        and the top 5 performance optimization opportunities ranked by potential time savings.
        This uses Google's real Lighthouse engine — the same tool Chrome DevTools uses.
        Takes 15-30 seconds to complete.
        """
        result = analyze_pagespeed(url, strategy)
        result["url"] = url
        return result

    @mcp.tool(
        tags={"audit", "links"},
        annotations={"readOnlyHint": True},
    )
    def check_links(
        url: Annotated[str, Field(description="URL to scan for broken links (e.g., 'example.com' or 'https://example.com')")],
    ) -> dict:
        """Scan a page for broken links — find 404s, redirects, timeouts, and server errors.

        Extracts all links (internal + external) from the page, checks each with
        a HEAD request, and groups results by status: working (2xx), redirects (3xx),
        client errors (4xx), server errors (5xx), and timeouts.
        Checks up to 50 links concurrently for speed. Results cached for 5 minutes.
        """
        normalized = _normalize_url(url)

        # Check cache first
        cache_key = f"links:{normalized}"
        if cache_key in _link_check_cache:
            cached, expiry = _link_check_cache[cache_key]
            if time.time() < expiry:
                return cached

        # Fetch the page and extract links
        resp, soup = fetch_page(url)
        actual_url = resp.url

        # Collect all <a href="..."> links
        skip_prefixes = ("mailto:", "tel:", "javascript:", "#", "data:")
        seen: set[str] = set()
        raw_links: list[dict] = []

        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            if not href or any(href.startswith(p) for p in skip_prefixes):
                continue
            # Resolve relative URLs
            full_url = urljoin(actual_url, href)
            if full_url in seen:
                continue
            seen.add(full_url)
            text = (tag.get_text(strip=True) or "")[:80]
            raw_links.append({"url": full_url, "text": text})

        total_found = len(raw_links)
        # Cap at 50 links to avoid taking forever
        links_to_check = raw_links[:50]
        skipped = total_found - len(links_to_check)

        def _check_single_link(link: dict) -> dict:
            """Check a single link with HEAD request, follow redirects manually."""
            link_url = link["url"]
            result = {"url": link_url, "text": link["text"]}
            redirects = []
            current = link_url
            max_hops = 5

            try:
                for _ in range(max_hops):
                    head_resp = SESSION.head(
                        current, timeout=5, allow_redirects=False
                    )
                    status = head_resp.status_code
                    if 300 <= status < 400:
                        location = head_resp.headers.get("Location", "")
                        if location:
                            location = urljoin(current, location)
                            redirects.append({"from": current, "to": location, "status": status})
                            current = location
                        else:
                            break
                    else:
                        break

                result["status_code"] = status
                result["final_url"] = current
                if redirects:
                    result["redirect_chain"] = redirects

                if 200 <= status < 300:
                    result["category"] = "working"
                elif 300 <= status < 400:
                    result["category"] = "redirect"
                elif 400 <= status < 500:
                    result["category"] = "client_error"
                elif 500 <= status < 600:
                    result["category"] = "server_error"
                else:
                    result["category"] = "other"

            except requests.exceptions.Timeout:
                result["status_code"] = None
                result["category"] = "timeout"
                result["error"] = "Request timed out (5s)"
            except requests.exceptions.ConnectionError:
                result["status_code"] = None
                result["category"] = "connection_error"
                result["error"] = "Could not connect"
            except requests.RequestException as e:
                result["status_code"] = None
                result["category"] = "error"
                result["error"] = str(e)[:100]

            return result

        # Check links concurrently
        results: list[dict] = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(_check_single_link, link): link for link in links_to_check}
            for future in as_completed(futures):
                results.append(future.result())

        # Group by category
        working = [r for r in results if r["category"] == "working"]
        redirects = [r for r in results if r["category"] == "redirect"]
        client_errors = [r for r in results if r["category"] == "client_error"]
        server_errors = [r for r in results if r["category"] == "server_error"]
        timeouts = [r for r in results if r["category"] == "timeout"]
        connection_errors = [r for r in results if r["category"] == "connection_error"]
        other_errors = [r for r in results if r["category"] in ("error", "other")]

        # Determine internal vs external
        parsed_base = urlparse(actual_url)
        base_domain = parsed_base.netloc
        internal = [r for r in results if urlparse(r["url"]).netloc == base_domain]
        external = [r for r in results if urlparse(r["url"]).netloc != base_domain]

        # Build broken links detail (only non-working)
        broken = client_errors + server_errors + timeouts + connection_errors + other_errors

        output = {
            "url": actual_url,
            "total_links_found": total_found,
            "links_checked": len(links_to_check),
            "links_skipped": skipped,
            "summary": {
                "working": len(working),
                "redirects": len(redirects),
                "client_errors_4xx": len(client_errors),
                "server_errors_5xx": len(server_errors),
                "timeouts": len(timeouts),
                "connection_errors": len(connection_errors),
                "other_errors": len(other_errors),
            },
            "internal_links": len(internal),
            "external_links": len(external),
            "broken_links": [
                {k: v for k, v in r.items() if k != "category"}
                for r in broken
            ],
            "redirect_chains": [
                {k: v for k, v in r.items() if k != "category"}
                for r in redirects
            ],
        }

        # Cache the result
        _link_check_cache[cache_key] = (output, time.time() + _LINK_CACHE_TTL)

        return output

    @mcp.tool(
        tags={"audit", "check"},
        annotations={"readOnlyHint": True},
    )
    def check_robots_txt(
        url: Annotated[str, Field(description="Website URL or domain to check robots.txt")],
    ) -> dict:
        """Check and analyze a site's robots.txt file.

        Shows which paths are allowed/disallowed, sitemaps referenced,
        and crawl-delay settings.
        """
        domain = get_domain(url)
        robots_url = f"https://{domain}/robots.txt"
        resp = fetch_url(robots_url)

        if resp is None or resp.status_code != 200:
            return {
                "url": robots_url,
                "exists": False,
                "note": "No robots.txt found — search engines will crawl everything",
            }

        content = resp.text
        lines = content.strip().split("\n")
        rules = []
        sitemaps = []
        current_agent = "*"

        for line in lines:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            if line.lower().startswith("user-agent:"):
                current_agent = line.split(":", 1)[1].strip()
            elif line.lower().startswith("disallow:"):
                path = line.split(":", 1)[1].strip()
                if path:
                    rules.append({"agent": current_agent, "type": "disallow", "path": path})
            elif line.lower().startswith("allow:"):
                path = line.split(":", 1)[1].strip()
                if path:
                    rules.append({"agent": current_agent, "type": "allow", "path": path})
            elif line.lower().startswith("sitemap:"):
                sitemaps.append(line.split(":", 1)[1].strip())

        return {
            "url": robots_url,
            "exists": True,
            "rules_count": len(rules),
            "rules": rules[:30],
            "sitemaps": sitemaps,
            "raw_length": len(content),
        }


def _score_to_grade(score: int) -> str:
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"
