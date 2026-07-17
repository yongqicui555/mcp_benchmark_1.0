"""Tests for analytics, health check, and preferences tools."""

from __future__ import annotations

import json

import pytest
import respx
from httpx import Response

from youfiliate_mcp.client import YoufiliateClient
from youfiliate_mcp.config import settings
from youfiliate_mcp.schemas.analytics import (
    CheckLinkHealthInput,
    GetAggregateStatsInput,
    GetPreferencesInput,
    GetSmartLinkStatsInput,
    UpdatePreferencesInput,
)
from youfiliate_mcp.tools.analytics import register_analytics_tools
from youfiliate_mcp.tools.preferences import register_preferences_tools

from .conftest import SAMPLE_SMART_LINK, SAMPLE_STATS

BASE = settings.youfiliate_api_base_url


class TestGetSmartLinkStats:
    @pytest.mark.asyncio
    async def test_stats_markdown(self, mock_api, client: YoufiliateClient) -> None:
        link_id = SAMPLE_SMART_LINK["id"]
        mock_api.get(f"{BASE}/api/smart-links/{link_id}/stats/").mock(
            return_value=Response(200, json=SAMPLE_STATS)
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_analytics_tools(mcp, client)

        params = GetSmartLinkStatsInput(id=link_id, period="30d")
        tool = mcp._tool_manager._tools["youfiliate_get_smart_link_stats"]
        result = await tool.fn(params)

        assert "Smart Link Stats" in result
        assert "1234" in result  # total clicks
        assert "US" in result
        assert "youtube.com" in result

    @pytest.mark.asyncio
    async def test_stats_json(self, mock_api, client: YoufiliateClient) -> None:
        link_id = SAMPLE_SMART_LINK["id"]
        mock_api.get(f"{BASE}/api/smart-links/{link_id}/stats/").mock(
            return_value=Response(200, json=SAMPLE_STATS)
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_analytics_tools(mcp, client)

        params = GetSmartLinkStatsInput(id=link_id, period="7d", response_format="json")
        tool = mcp._tool_manager._tools["youfiliate_get_smart_link_stats"]
        result = await tool.fn(params)

        parsed = json.loads(result)
        assert parsed["summary"]["total_clicks"] == 1234


class TestGetAggregateStats:
    @pytest.mark.asyncio
    async def test_aggregate_stats(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.get(f"{BASE}/api/smart-links/aggregate-stats/").mock(
            return_value=Response(200, json=SAMPLE_STATS)
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_analytics_tools(mcp, client)

        params = GetAggregateStatsInput(period="30d")
        tool = mcp._tool_manager._tools["youfiliate_get_aggregate_stats"]
        result = await tool.fn(params)

        assert "Aggregate Stats" in result
        assert "1234" in result


class TestCheckLinkHealth:
    @pytest.mark.asyncio
    async def test_health_check(self, mock_api, client: YoufiliateClient) -> None:
        link_id = SAMPLE_SMART_LINK["id"]
        mock_api.post(f"{BASE}/api/smart-links/{link_id}/check-health/").mock(
            return_value=Response(200, json={
                "health_status": "healthy",
                "checks": [
                    {
                        "url": "https://amazon.com/dp/B09V3KXJPB",
                        "is_healthy": True,
                        "status_code": 200,
                        "response_time_ms": 150,
                    },
                ],
            })
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_analytics_tools(mcp, client)

        params = CheckLinkHealthInput(id=link_id)
        tool = mcp._tool_manager._tools["youfiliate_check_link_health"]
        result = await tool.fn(params)

        assert "Health Check" in result
        assert "healthy" in result.lower()
        assert "OK" in result

    @pytest.mark.asyncio
    async def test_health_check_rate_limited(self, mock_api, client: YoufiliateClient) -> None:
        link_id = SAMPLE_SMART_LINK["id"]
        mock_api.post(f"{BASE}/api/smart-links/{link_id}/check-health/").mock(
            return_value=Response(429, json={"detail": "Rate limit: one check per 5 minutes."})
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_analytics_tools(mcp, client)

        params = CheckLinkHealthInput(id=link_id)
        tool = mcp._tool_manager._tools["youfiliate_check_link_health"]
        result = await tool.fn(params)

        assert "Error" in result
        assert "rate" in result.lower() or "Rate" in result


class TestPreferences:
    @pytest.mark.asyncio
    async def test_get_preferences(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.get(f"{BASE}/api/smart-links/preferences/").mock(
            return_value=Response(200, json={
                "default_redirect_type": "302",
                "default_geo_rules_enabled": True,
                "default_deep_linking_enabled": False,
            })
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_preferences_tools(mcp, client)

        params = GetPreferencesInput()
        tool = mcp._tool_manager._tools["youfiliate_get_preferences"]
        result = await tool.fn(params)

        assert "Preferences" in result
        assert "302" in result

    @pytest.mark.asyncio
    async def test_update_preferences(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.patch(f"{BASE}/api/smart-links/preferences/").mock(
            return_value=Response(200, json={
                "default_redirect_type": "301",
                "default_geo_rules_enabled": True,
                "default_deep_linking_enabled": True,
            })
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_preferences_tools(mcp, client)

        params = UpdatePreferencesInput(default_redirect_type="301", default_deep_linking_enabled=True)
        tool = mcp._tool_manager._tools["youfiliate_update_preferences"]
        result = await tool.fn(params)

        assert "Updated" in result
        assert "301" in result

    @pytest.mark.asyncio
    async def test_update_no_fields(self, mock_api, client: YoufiliateClient) -> None:
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_preferences_tools(mcp, client)

        params = UpdatePreferencesInput()
        tool = mcp._tool_manager._tools["youfiliate_update_preferences"]
        result = await tool.fn(params)

        assert "Error" in result
