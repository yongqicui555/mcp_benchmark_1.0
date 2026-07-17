"""Feedback Synthesis MCP — Thin client that proxies to hosted backend with x402 auto-payment."""

import os
from typing import Any

from fastmcp import FastMCP

from feedback_synthesis_mcp.client import FeedbackSynthesisClient

mcp = FastMCP(
    name="feedback-synthesis-mcp",
    version="0.1.0",
    instructions=(
        "Customer feedback intelligence for developers and AI agents. "
        "4 tools: synthesize_feedback ($0.05), get_pain_points ($0.02), "
        "search_feedback ($0.01), get_sentiment_trends ($0.03). "
        "Requires EVM_PRIVATE_KEY for x402 payments (USDC on Base mainnet). "
        "Sources: GitHub Issues, Hacker News, App Store Reviews."
    ),
)

_client = None


def _get_client() -> FeedbackSynthesisClient:
    global _client
    if _client is None:
        _client = FeedbackSynthesisClient(
            backend_url=os.environ.get(
                "FEEDBACK_SYNTHESIS_BACKEND_URL",
                "https://feedback-synthesis-mcp-production.up.railway.app",
            ),
            private_key=os.environ.get("EVM_PRIVATE_KEY", ""),
        )
    return _client


@mcp.tool()
def synthesize_feedback(
    sources: list[dict] = None,
    max_items_per_source: int = 200,
    since: str | None = None,
    focus: str = "pain_points",
) -> dict[str, Any]:
    """Synthesize customer feedback from multiple sources into ranked pain clusters.

    Collects feedback from GitHub Issues, Hacker News, and/or App Store Reviews,
    then runs a multi-pass LLM pipeline to extract and rank pain clusters with evidence.
    Returns up to 10 ranked pain clusters with impact scores, evidence links, and
    suggested actions. Takes 10-60 seconds depending on volume.

    Args:
        sources: List of source specs. Each has 'type' (github_issues/hackernews/appstore)
                 and 'target' (owner/repo, search query, or app bundle ID).
                 Example: [{"type": "github_issues", "target": "owner/repo"},
                           {"type": "hackernews", "target": "MyProduct"}]
        max_items_per_source: Max feedback items to collect per source (default 200)
        since: ISO 8601 datetime to filter items (e.g. '2026-01-01T00:00:00Z')
        focus: Analysis focus — 'pain_points' (default) or 'feature_requests'
    """
    if not sources:
        return {"error": "Missing required parameter: 'sources' list with at least one source spec."}
    return _get_client().call(
        "synthesize_feedback",
        sources=sources,
        max_items_per_source=max_items_per_source,
        since=since,
        focus=focus,
    )


@mcp.tool()
def get_pain_points(
    source: dict = None,
    max_items: int = 100,
    top_n: int = 5,
) -> dict[str, Any]:
    """Quickly extract top pain points from a single feedback source.

    Faster and cheaper than synthesize_feedback — single LLM pass, one source.
    Returns the top N pain points with frequency counts and sample evidence URLs.

    Args:
        source: Source spec with 'type' (github_issues/hackernews/appstore) and 'target'.
                Example: {"type": "github_issues", "target": "owner/repo", "labels": ["bug"]}
        max_items: Max items to collect (default 100)
        top_n: Number of top pain points to return (default 5)
    """
    if not source:
        return {"error": "Missing required parameter: 'source' dict with type and target."}
    return _get_client().call(
        "get_pain_points",
        source=source,
        max_items=max_items,
        top_n=top_n,
    )


@mcp.tool()
def search_feedback(
    query: str = "",
    sources: list[str] | None = None,
    target: str = "",
    since: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Search raw feedback items across cached sources using full-text search.

    Useful for drilling into a specific topic after synthesis. Searches previously
    collected feedback without triggering new LLM processing. Fast and cheap.

    Args:
        query: Search terms (e.g. 'authentication mobile' or 'pricing too expensive')
        sources: Filter by source types (e.g. ['github_issues', 'appstore'])
        target: Filter by target repo/app (e.g. 'owner/repo')
        since: ISO 8601 datetime filter (e.g. '2026-01-01T00:00:00Z')
        limit: Max results to return (default 20)
    """
    if not query:
        return {"error": "Missing required parameter: 'query' search string."}
    return _get_client().call(
        "search_feedback",
        query=query,
        sources=sources,
        target=target,
        since=since,
        limit=limit,
    )


@mcp.tool()
def get_sentiment_trends(
    sources: list[dict] = None,
    since: str = "2025-10-01T00:00:00Z",
    granularity: str = "weekly",
) -> dict[str, Any]:
    """Get time-series sentiment analysis across feedback sources.

    Shows how sentiment shifts over time — useful for tracking the impact of
    releases, bug fixes, or feature launches. Returns weekly/monthly sentiment
    scores with notable shifts and likely causes.

    Args:
        sources: List of source specs (same format as synthesize_feedback)
        since: Start date for trend analysis (ISO 8601, default 6 months ago)
        granularity: Time bucket size — 'weekly' (default) or 'monthly'
    """
    if not sources:
        return {"error": "Missing required parameter: 'sources' list with at least one source spec."}
    return _get_client().call(
        "get_sentiment_trends",
        sources=sources,
        since=since,
        granularity=granularity,
    )
