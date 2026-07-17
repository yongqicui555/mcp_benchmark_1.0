"""Google PageSpeed Insights integration — Lighthouse scores and Core Web Vitals."""

import requests
from fastmcp.exceptions import ToolError

PAGESPEED_API = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def analyze_pagespeed(url: str, strategy: str = "mobile") -> dict:
    """Run Google PageSpeed Insights on a URL. Returns Lighthouse scores and Core Web Vitals."""
    if not url.startswith("http"):
        url = f"https://{url}"

    try:
        resp = requests.get(
            PAGESPEED_API,
            params={
                "url": url,
                "strategy": strategy,
                "category": ["performance", "accessibility", "best-practices", "seo"],
            },
            timeout=60,  # PageSpeed can take 30+ seconds
        )
        if resp.status_code == 429:
            return {"error": "PageSpeed API rate limit reached. Wait a minute and try again.", "available": False}
        if resp.status_code != 200:
            return {"error": f"PageSpeed API returned {resp.status_code}", "available": False}
        data = resp.json()
    except ToolError:
        raise
    except requests.RequestException as e:
        return {"error": str(e), "available": False}

    result = {"available": True, "strategy": strategy}

    # Lighthouse scores
    categories = data.get("lighthouseResult", {}).get("categories", {})
    result["lighthouse_scores"] = {}
    for cat_id, cat_data in categories.items():
        score = cat_data.get("score")
        result["lighthouse_scores"][cat_id] = round(score * 100) if score is not None else None

    # Core Web Vitals from CrUX field data
    loading = data.get("loadingExperience", {})
    metrics = loading.get("metrics", {})
    cwv = {}
    metric_map = {
        "LARGEST_CONTENTFUL_PAINT_MS": "lcp_ms",
        "INTERACTION_TO_NEXT_PAINT": "inp_ms",
        "CUMULATIVE_LAYOUT_SHIFT_SCORE": "cls",
        "FIRST_CONTENTFUL_PAINT_MS": "fcp_ms",
        "EXPERIMENTAL_TIME_TO_FIRST_BYTE": "ttfb_ms",
    }
    for api_key, name in metric_map.items():
        if api_key in metrics:
            m = metrics[api_key]
            cwv[name] = {
                "value": m.get("percentile"),
                "category": m.get("category", "").lower(),  # FAST, AVERAGE, SLOW
            }

    result["core_web_vitals"] = cwv if cwv else {"note": "No field data available (site may have low Chrome traffic)"}
    result["overall_category"] = loading.get("overall_category", "unknown").lower()

    # Key Lighthouse audits (actionable recommendations)
    audits = data.get("lighthouseResult", {}).get("audits", {})
    opportunities = []
    for audit_id, audit in audits.items():
        score = audit.get("score")
        if score is not None and score < 0.9 and audit.get("details", {}).get("type") == "opportunity":
            savings = audit.get("details", {}).get("overallSavingsMs")
            opportunities.append({
                "id": audit_id,
                "title": audit.get("title", audit_id),
                "savings_ms": savings,
                "description": audit.get("description", "")[:120],
            })
    # Sort by savings
    opportunities.sort(key=lambda x: x.get("savings_ms") or 0, reverse=True)
    result["top_opportunities"] = opportunities[:5]

    return result
