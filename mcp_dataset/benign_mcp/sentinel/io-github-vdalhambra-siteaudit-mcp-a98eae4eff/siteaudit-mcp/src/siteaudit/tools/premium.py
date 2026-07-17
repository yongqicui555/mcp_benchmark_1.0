"""Premium tools for SiteAudit MCP — v1.2.0.

Advanced audit tools available in Pro tier and above on MCPize.
Self-hosted users have access to all tools.
"""

import json
from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP

from siteaudit.utils.fetcher import fetch_page


def register_premium_tools(mcp: FastMCP) -> None:
    """Register premium/advanced tools on the MCP server."""

    @mcp.tool(
        tags={"audit", "accessibility", "premium"},
        annotations={"readOnlyHint": True},
    )
    def accessibility_audit(
        url: Annotated[str, Field(description="URL to audit (e.g., 'example.com')")],
    ) -> dict:
        """Run WCAG accessibility checks on a URL.

        Returns a score (0-100) and detailed findings on:
        - Missing alt text on images
        - Form inputs without labels
        - Heading hierarchy issues
        - Color contrast hints (limited without rendering)
        - ARIA attribute usage
        - Language declaration
        - Skip links
        - Focus indicators (heuristic)
        """
        resp, soup = fetch_page(url)
        actual_url = resp.url

        issues = []
        warnings = []
        passes = []

        # 1. Language declaration
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            passes.append({"check": "lang_attribute", "value": html_tag.get("lang")})
        else:
            issues.append({
                "severity": "high",
                "check": "missing_lang",
                "message": "HTML element missing 'lang' attribute",
                "wcag": "3.1.1 Language of Page",
            })

        # 2. Images without alt text
        images = soup.find_all("img")
        missing_alt = [img for img in images if not img.get("alt") and not img.get("role") == "presentation"]
        if images:
            alt_coverage = (len(images) - len(missing_alt)) / len(images) * 100
            if missing_alt:
                issues.append({
                    "severity": "high" if len(missing_alt) > 5 else "medium",
                    "check": "missing_alt",
                    "message": f"{len(missing_alt)} of {len(images)} images missing alt text",
                    "coverage_pct": round(alt_coverage, 1),
                    "wcag": "1.1.1 Non-text Content",
                })
            else:
                passes.append({"check": "alt_coverage", "message": f"All {len(images)} images have alt text"})

        # 3. Form inputs without labels
        inputs = soup.find_all(["input", "textarea", "select"])
        unlabeled = []
        for inp in inputs:
            if inp.get("type") in ("hidden", "submit", "button"):
                continue
            input_id = inp.get("id")
            aria_label = inp.get("aria-label")
            aria_labelledby = inp.get("aria-labelledby")
            # Check if there's a label with for=id
            has_label = False
            if input_id:
                label = soup.find("label", {"for": input_id})
                has_label = label is not None
            # Check if wrapped in a label
            parent_label = inp.find_parent("label")
            if not (has_label or parent_label or aria_label or aria_labelledby):
                unlabeled.append(inp.get("name") or inp.get("type", "unknown"))
        if inputs:
            if unlabeled:
                issues.append({
                    "severity": "high",
                    "check": "unlabeled_inputs",
                    "message": f"{len(unlabeled)} of {len(inputs)} form inputs lack labels",
                    "examples": unlabeled[:5],
                    "wcag": "1.3.1 Info and Relationships, 3.3.2 Labels or Instructions",
                })
            else:
                passes.append({"check": "form_labels", "message": f"All {len(inputs)} inputs have labels"})

        # 4. Heading hierarchy
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        h1_count = len([h for h in headings if h.name == "h1"])
        if h1_count == 0:
            issues.append({
                "severity": "high",
                "check": "no_h1",
                "message": "No H1 heading found",
                "wcag": "1.3.1 Info and Relationships, 2.4.6 Headings and Labels",
            })
        elif h1_count > 1:
            warnings.append({
                "severity": "medium",
                "check": "multiple_h1",
                "message": f"Multiple H1 headings ({h1_count}). Recommend one per page.",
            })
        else:
            passes.append({"check": "single_h1", "message": "Exactly one H1 heading"})

        # Check for skipped heading levels
        prev_level = 0
        skipped = []
        for h in headings:
            level = int(h.name[1])
            if prev_level > 0 and level > prev_level + 1:
                skipped.append({"from": f"h{prev_level}", "to": h.name, "text": h.get_text(strip=True)[:50]})
            prev_level = level
        if skipped:
            warnings.append({
                "severity": "medium",
                "check": "skipped_heading_levels",
                "message": f"Skipped heading levels {len(skipped)} times",
                "examples": skipped[:3],
            })

        # 5. Links with no text
        links = soup.find_all("a", href=True)
        empty_links = [a for a in links if not a.get_text(strip=True) and not a.get("aria-label") and not a.find("img", alt=True)]
        if empty_links:
            issues.append({
                "severity": "high",
                "check": "empty_links",
                "message": f"{len(empty_links)} links have no accessible text",
                "wcag": "2.4.4 Link Purpose",
            })

        # 6. Skip link detection
        skip_link = soup.find("a", href="#main") or soup.find("a", href="#content") or soup.find("a", class_=lambda c: c and "skip" in c.lower() if c else False)
        if skip_link:
            passes.append({"check": "skip_link", "message": "Skip navigation link found"})
        else:
            warnings.append({
                "severity": "low",
                "check": "no_skip_link",
                "message": "No skip navigation link detected",
                "wcag": "2.4.1 Bypass Blocks",
            })

        # 7. ARIA landmark roles
        landmarks = soup.find_all(attrs={"role": True})
        landmark_roles = set(el.get("role") for el in landmarks)
        semantic_tags = [soup.find(tag) for tag in ["main", "nav", "header", "footer"]]
        has_main = soup.find("main") or "main" in landmark_roles
        if not has_main:
            warnings.append({
                "severity": "medium",
                "check": "no_main_landmark",
                "message": "No <main> element or role='main' found",
                "wcag": "1.3.1 Info and Relationships",
            })
        else:
            passes.append({"check": "main_landmark"})

        # 8. Buttons without accessible name
        buttons = soup.find_all("button")
        unnamed_buttons = [b for b in buttons if not b.get_text(strip=True) and not b.get("aria-label")]
        if unnamed_buttons:
            issues.append({
                "severity": "high",
                "check": "unnamed_buttons",
                "message": f"{len(unnamed_buttons)} buttons have no accessible name",
                "wcag": "4.1.2 Name, Role, Value",
            })

        # Calculate score (deduction-based)
        score = 100
        for issue in issues:
            if issue.get("severity") == "high":
                score -= 15
            elif issue.get("severity") == "medium":
                score -= 8
            else:
                score -= 3
        for warn in warnings:
            if warn.get("severity") == "medium":
                score -= 4
            else:
                score -= 2
        score = max(0, min(100, score))

        grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 45 else "F"

        return {
            "url": actual_url,
            "score": score,
            "grade": grade,
            "summary": {
                "issues_count": len(issues),
                "warnings_count": len(warnings),
                "passes_count": len(passes),
                "images_total": len(images),
                "images_with_alt": len(images) - len(missing_alt) if images else 0,
                "form_inputs": len(inputs),
                "inputs_with_labels": len(inputs) - len(unlabeled) if inputs else 0,
                "headings_total": len(headings),
                "h1_count": h1_count,
            },
            "issues": issues,
            "warnings": warnings,
            "passes": passes,
            "note": "Limited without browser rendering. For full audit (color contrast, focus, keyboard nav), use axe-core.",
        }

    @mcp.tool(
        tags={"audit", "schema", "premium"},
        annotations={"readOnlyHint": True},
    )
    def schema_validator(
        url: Annotated[str, Field(description="URL to check for structured data (Schema.org)")],
    ) -> dict:
        """Extract and validate Schema.org structured data (JSON-LD, microdata).

        Returns all structured data found on the page with validation hints
        and a breakdown by schema type. Critical for rich snippets in SERPs.
        """
        resp, soup = fetch_page(url)
        actual_url = resp.url

        # Extract JSON-LD blocks
        json_ld_blocks = soup.find_all("script", type="application/ld+json")
        schemas = []
        errors = []

        for i, block in enumerate(json_ld_blocks):
            raw = block.string or block.get_text()
            if not raw:
                continue
            try:
                data = json.loads(raw)
                # Can be a single object or array
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    schema_type = item.get("@type", "Unknown")
                    schema_context = item.get("@context", "")
                    # Handle array types
                    type_str = schema_type if isinstance(schema_type, str) else "/".join(schema_type) if isinstance(schema_type, list) else str(schema_type)

                    # Basic validation
                    validation = {"valid": True, "warnings": []}
                    if not schema_context:
                        validation["warnings"].append("Missing @context")
                    elif "schema.org" not in str(schema_context):
                        validation["warnings"].append(f"Non-standard @context: {schema_context}")

                    # Check for required fields by type
                    required_by_type = {
                        "Product": ["name", "offers"],
                        "Article": ["headline", "author", "datePublished"],
                        "Organization": ["name", "url"],
                        "Person": ["name"],
                        "WebSite": ["name", "url"],
                        "BreadcrumbList": ["itemListElement"],
                        "FAQPage": ["mainEntity"],
                        "Recipe": ["name", "recipeIngredient", "recipeInstructions"],
                        "Event": ["name", "startDate", "location"],
                        "LocalBusiness": ["name", "address"],
                    }
                    missing = []
                    for req in required_by_type.get(type_str, []):
                        if req not in item:
                            missing.append(req)
                    if missing:
                        validation["valid"] = False
                        validation["warnings"].append(f"Missing recommended fields for {type_str}: {', '.join(missing)}")

                    schemas.append({
                        "block_index": i,
                        "type": type_str,
                        "context": schema_context if isinstance(schema_context, str) else str(schema_context),
                        "keys": list(item.keys()),
                        "validation": validation,
                    })
            except json.JSONDecodeError as e:
                errors.append({
                    "block_index": i,
                    "error": f"Invalid JSON: {str(e)}",
                    "preview": raw[:200],
                })

        # Extract microdata (itemscope/itemtype)
        microdata_items = soup.find_all(attrs={"itemscope": True})
        microdata = [{"itemtype": item.get("itemtype", "Unknown"), "tag": item.name} for item in microdata_items[:10]]

        # Extract Open Graph
        og_tags = soup.find_all("meta", attrs={"property": lambda x: x and x.startswith("og:")})
        og = {t.get("property"): t.get("content", "") for t in og_tags}

        # Count by type
        type_counts = {}
        for s in schemas:
            t = s["type"]
            type_counts[t] = type_counts.get(t, 0) + 1

        # Score: penalize for errors, reward for schemas
        score = 0
        if json_ld_blocks:
            score += min(50, len(schemas) * 10)
        if og:
            score += 20
        if microdata:
            score += 10
        if not errors:
            score += 10
        invalid_schemas = sum(1 for s in schemas if not s["validation"]["valid"])
        score -= invalid_schemas * 5
        score = max(0, min(100, score))

        return {
            "url": actual_url,
            "score": score,
            "summary": {
                "json_ld_blocks": len(json_ld_blocks),
                "schemas_found": len(schemas),
                "types_used": list(type_counts.keys()),
                "type_counts": type_counts,
                "microdata_items": len(microdata_items),
                "open_graph_tags": len(og_tags),
                "parse_errors": len(errors),
                "invalid_schemas": invalid_schemas,
            },
            "schemas": schemas,
            "errors": errors,
            "microdata": microdata,
            "open_graph": og,
        }

    @mcp.tool(
        tags={"audit", "competitors", "premium"},
        annotations={"readOnlyHint": True},
    )
    def competitor_gap_analysis(
        your_url: Annotated[str, Field(description="Your website URL")],
        competitor_urls: Annotated[str, Field(description="Comma-separated competitor URLs (up to 5)")],
    ) -> dict:
        """Analyze SEO/security/performance gaps vs competitors.

        Returns areas where competitors outperform your site,
        with specific recommendations for improvement.
        """
        from siteaudit.analyzers.seo import analyze_seo
        from siteaudit.analyzers.security import analyze_security
        from siteaudit.analyzers.performance import analyze_performance

        def audit_site(url):
            try:
                resp, soup = fetch_page(url)
                seo = analyze_seo(resp.url, resp, soup)
                sec = analyze_security(resp.url, resp)
                perf = analyze_performance(resp.url, resp)
                return {
                    "url": resp.url,
                    "seo": seo["score"],
                    "security": sec["score"],
                    "performance": perf["score"],
                    "seo_issues": seo.get("issues", [])[:5],
                    "security_issues": sec.get("issues", [])[:5],
                    "performance_issues": perf.get("issues", [])[:5],
                }
            except Exception as e:
                return {"url": url, "error": str(e)}

        yours = audit_site(your_url)
        competitors = [audit_site(u.strip()) for u in competitor_urls.split(",") if u.strip()][:5]

        if "error" in yours:
            return {"error": "Failed to audit your URL", "details": yours["error"]}

        valid_comps = [c for c in competitors if "error" not in c]
        if not valid_comps:
            return {"error": "Failed to audit any competitors", "your_audit": yours}

        # Calculate gaps
        avg_comp_seo = sum(c["seo"] for c in valid_comps) / len(valid_comps)
        avg_comp_sec = sum(c["security"] for c in valid_comps) / len(valid_comps)
        avg_comp_perf = sum(c["performance"] for c in valid_comps) / len(valid_comps)

        gaps = []
        if yours["seo"] < avg_comp_seo:
            gaps.append({
                "category": "SEO",
                "your_score": yours["seo"],
                "avg_competitor_score": round(avg_comp_seo, 1),
                "gap": round(avg_comp_seo - yours["seo"], 1),
                "priority": "HIGH" if avg_comp_seo - yours["seo"] > 15 else "MEDIUM",
            })
        if yours["security"] < avg_comp_sec:
            gaps.append({
                "category": "Security",
                "your_score": yours["security"],
                "avg_competitor_score": round(avg_comp_sec, 1),
                "gap": round(avg_comp_sec - yours["security"], 1),
                "priority": "HIGH" if avg_comp_sec - yours["security"] > 15 else "MEDIUM",
            })
        if yours["performance"] < avg_comp_perf:
            gaps.append({
                "category": "Performance",
                "your_score": yours["performance"],
                "avg_competitor_score": round(avg_comp_perf, 1),
                "gap": round(avg_comp_perf - yours["performance"], 1),
                "priority": "HIGH" if avg_comp_perf - yours["performance"] > 15 else "MEDIUM",
            })

        # Find strengths
        strengths = []
        if yours["seo"] > avg_comp_seo:
            strengths.append({"category": "SEO", "advantage": round(yours["seo"] - avg_comp_seo, 1)})
        if yours["security"] > avg_comp_sec:
            strengths.append({"category": "Security", "advantage": round(yours["security"] - avg_comp_sec, 1)})
        if yours["performance"] > avg_comp_perf:
            strengths.append({"category": "Performance", "advantage": round(yours["performance"] - avg_comp_perf, 1)})

        # Best competitor per category
        best_seo = max(valid_comps, key=lambda c: c["seo"])
        best_sec = max(valid_comps, key=lambda c: c["security"])
        best_perf = max(valid_comps, key=lambda c: c["performance"])

        return {
            "your_site": yours,
            "competitors_analyzed": len(valid_comps),
            "competitor_results": competitors,
            "averages": {
                "seo": round(avg_comp_seo, 1),
                "security": round(avg_comp_sec, 1),
                "performance": round(avg_comp_perf, 1),
            },
            "your_gaps": gaps,
            "your_strengths": strengths,
            "best_performers": {
                "seo": {"url": best_seo["url"], "score": best_seo["seo"]},
                "security": {"url": best_sec["url"], "score": best_sec["security"]},
                "performance": {"url": best_perf["url"], "score": best_perf["performance"]},
            },
            "priority_focus": gaps[0]["category"] if gaps else "None — you're leading",
        }
