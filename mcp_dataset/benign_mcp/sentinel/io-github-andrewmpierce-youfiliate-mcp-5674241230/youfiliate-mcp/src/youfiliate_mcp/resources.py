"""MCP resources for Youfiliate Smart Links.

Resources:
  - youfiliate://summary         — Dashboard summary
  - youfiliate://preferences     — Current preferences
  - youfiliate://smart-link/{id} — Single smart link details
  - youfiliate://plan-limits     — Plan usage and limits
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import YoufiliateClient, make_api_call


def register_resources(mcp: FastMCP, client: YoufiliateClient) -> None:
    """Register all MCP resources."""

    @mcp.resource("youfiliate://summary")
    async def get_summary() -> str:
        """Dashboard summary: link counts, total clicks, health overview, plan limit.

        Provides a quick overview of your Youfiliate account including
        how many smart links you have, total clicks, and health status
        breakdown. Useful context for the LLM to understand your account state.
        """
        ok, result = await make_api_call(client, "GET", "/api/smart-links/summary/")
        if not ok:
            return f"Error loading summary: {result}"
        return json.dumps(result, indent=2)

    @mcp.resource("youfiliate://preferences")
    async def get_preferences() -> str:
        """Current smart link preferences (read-only view).

        Returns default settings for new smart links including redirect type,
        geo-targeting, and deep linking defaults.
        """
        ok, result = await make_api_call(client, "GET", "/api/smart-links/preferences/")
        if not ok:
            return f"Error loading preferences: {result}"
        return json.dumps(result, indent=2)

    @mcp.resource("youfiliate://smart-link/{id}")
    async def get_smart_link(id: str) -> str:
        """Read-only view of a single smart link by ID.

        Faster than the tool for simple lookups — returns full smart link
        details including geo rules, deep link config, and click stats.
        """
        ok, result = await make_api_call(client, "GET", f"/api/smart-links/{id}/")
        if not ok:
            return f"Error loading smart link: {result}"
        return json.dumps(result, indent=2)

    @mcp.resource("youfiliate://plan-limits")
    async def get_plan_limits() -> str:
        """Current plan and usage (links used / limit).

        Returns the user's current plan tier, how many smart links they've
        used, and their plan limit. Useful context for the LLM to know
        if the user can create more links.
        """
        ok, result = await make_api_call(client, "GET", "/api/smart-links/plan-limits/")
        if not ok:
            # Fallback: try to get this from the user profile
            ok2, user_data = await make_api_call(client, "GET", "/api/auth/me/")
            if ok2:
                return json.dumps({
                    "plan": user_data.get("smart_link_plan", "free"),
                    "note": "Detailed plan limits endpoint not available",
                }, indent=2)
            return f"Error loading plan limits: {result}"
        return json.dumps(result, indent=2)
