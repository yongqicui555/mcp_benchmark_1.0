"""Analytics and health-check tools (3 tools).

Tools:
  - youfiliate_get_smart_link_stats
  - youfiliate_get_aggregate_stats
  - youfiliate_check_link_health
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import YoufiliateClient, make_api_call
from ..config import settings as app_settings
from ..schemas.analytics import (
    CheckLinkHealthInput,
    GetAggregateStatsInput,
    GetSmartLinkStatsInput,
)
from ..schemas.common import ResponseFormat


def _truncate(text: str) -> str:
    limit = app_settings.max_response_chars
    if len(text) > limit:
        return text[:limit] + "\n\n[Truncated — use filters or pagination to narrow results]"
    return text


def _format_stats_markdown(data: dict[str, Any], title: str = "Click Stats") -> str:
    """Format click analytics as markdown."""
    lines = [f"# {title}", ""]

    summary = data.get("summary", data)
    lines.append(f"- **Total Clicks**: {summary.get('total_clicks', 0)}")
    lines.append(f"- **Unique Visitors**: {summary.get('unique_visitors', 0)}")
    lines.append(f"- **Period**: {data.get('period', 'N/A')}")
    lines.append("")

    by_country = data.get("by_country", [])
    if by_country:
        lines.append("## Clicks by Country")
        for entry in by_country[:20]:
            lines.append(f"- {entry.get('country_code', '??')}: {entry.get('clicks', 0)}")
        lines.append("")

    by_device = data.get("by_device", [])
    if by_device:
        lines.append("## Clicks by Device")
        for entry in by_device[:10]:
            lines.append(f"- {entry.get('device_type', '??')}: {entry.get('clicks', 0)}")
        lines.append("")

    by_referrer = data.get("by_referrer", [])
    if by_referrer:
        lines.append("## Top Referrers")
        for entry in by_referrer[:10]:
            lines.append(f"- {entry.get('referrer', 'direct')}: {entry.get('clicks', 0)}")
        lines.append("")

    by_day = data.get("by_day", [])
    if by_day:
        lines.append("## Daily Breakdown")
        for entry in by_day[:30]:
            lines.append(f"- {entry.get('date', '??')}: {entry.get('clicks', 0)} clicks")
        lines.append("")

    return "\n".join(lines)


def register_analytics_tools(mcp: FastMCP, client: YoufiliateClient) -> None:
    """Register analytics and health-check tools."""

    @mcp.tool(
        name="youfiliate_get_smart_link_stats",
        annotations={
            "title": "Get Smart Link Stats",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def youfiliate_get_smart_link_stats(params: GetSmartLinkStatsInput) -> str:
        """Get click analytics for a specific smart link.

        Returns click counts broken down by country, device, referrer,
        and day for the specified period. Does NOT modify any data.

        Common errors:
        - Smart link not found: check the ID.
        """
        ok, result = await make_api_call(
            client,
            "GET",
            f"/api/smart-links/{params.id}/stats/",
            params={"period": params.period},
        )
        if not ok:
            return result

        if params.response_format == ResponseFormat.JSON:
            return _truncate(json.dumps(result, indent=2))

        return _truncate(_format_stats_markdown(result, "Smart Link Stats"))

    @mcp.tool(
        name="youfiliate_get_aggregate_stats",
        annotations={
            "title": "Get Aggregate Stats",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def youfiliate_get_aggregate_stats(params: GetAggregateStatsInput) -> str:
        """Get aggregate click analytics across all your smart links.

        Returns total clicks, top countries, devices, and referrers
        across your entire account for the specified period.
        Does NOT modify any data.
        """
        ok, result = await make_api_call(
            client,
            "GET",
            "/api/smart-links/aggregate-stats/",
            params={"period": params.period},
        )
        if not ok:
            return result

        if params.response_format == ResponseFormat.JSON:
            return _truncate(json.dumps(result, indent=2))

        return _truncate(_format_stats_markdown(result, "Aggregate Stats (All Links)"))

    @mcp.tool(
        name="youfiliate_check_link_health",
        annotations={
            "title": "Check Link Health",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def youfiliate_check_link_health(params: CheckLinkHealthInput) -> str:
        """Trigger a health check for a specific smart link.

        Checks the default URL and all geo-rule URLs for availability.
        Returns the health status (healthy/broken/unknown).
        Rate limited to once per 5 minutes per link.
        Does NOT modify the link configuration.

        Common errors:
        - Rate limit: wait 5 minutes between health checks for the same link.
        - Smart link not found: check the ID.
        """
        ok, result = await make_api_call(
            client,
            "POST",
            f"/api/smart-links/{params.id}/check-health/",
        )
        if not ok:
            return result

        if params.response_format == ResponseFormat.JSON:
            return _truncate(json.dumps(result, indent=2))

        lines = ["# Health Check Results", ""]
        status = result.get("health_status", result.get("status", "unknown"))
        lines.append(f"- **Status**: {status}")

        checks = result.get("checks", [])
        if checks:
            lines.append("")
            lines.append("## URL Checks")
            for check in checks:
                icon = "OK" if check.get("is_healthy") else "FAIL"
                lines.append(
                    f"- [{icon}] {check.get('url', 'N/A')} — "
                    f"HTTP {check.get('status_code', '?')} "
                    f"({check.get('response_time_ms', '?')}ms)"
                )

        lines.append("")
        return _truncate("\n".join(lines))
