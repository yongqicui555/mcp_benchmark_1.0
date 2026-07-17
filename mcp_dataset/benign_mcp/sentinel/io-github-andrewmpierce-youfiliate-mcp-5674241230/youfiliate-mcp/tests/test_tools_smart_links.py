"""Tests for smart link CRUD tools."""

from __future__ import annotations

import json

import pytest
import respx
from httpx import Response

from youfiliate_mcp.client import YoufiliateClient
from youfiliate_mcp.config import settings
from youfiliate_mcp.schemas.smart_links import (
    CreateSmartLinkInput,
    DeleteSmartLinkInput,
    GetSmartLinkInput,
    ListSmartLinksInput,
    UpdateSmartLinkInput,
)
from youfiliate_mcp.server import create_server
from youfiliate_mcp.tools.smart_links import register_smart_link_tools

from .conftest import SAMPLE_SMART_LINK


BASE = settings.youfiliate_api_base_url


class TestCreateSmartLink:
    """Tests for youfiliate_create_smart_link."""

    @pytest.mark.asyncio
    async def test_create_basic(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.post(f"{BASE}/api/smart-links/").mock(
            return_value=Response(201, json=SAMPLE_SMART_LINK)
        )

        from youfiliate_mcp.tools.smart_links import register_smart_link_tools
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register_smart_link_tools(mcp, client)

        # Call the tool function directly
        params = CreateSmartLinkInput(
            default_url="https://amazon.com/dp/B09V3KXJPB",
            title="Test Smart Link",
        )

        # Access the registered tool function
        tools = mcp._tool_manager._tools
        tool = tools["youfiliate_create_smart_link"]
        result = await tool.fn(params)

        assert "Smart Link Created" in result
        assert "my-test-link" in result
        assert "youfil.to/" in result

    @pytest.mark.asyncio
    async def test_create_with_geo_rules(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.post(f"{BASE}/api/smart-links/").mock(
            return_value=Response(201, json=SAMPLE_SMART_LINK)
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_smart_link_tools(mcp, client)

        params = CreateSmartLinkInput(
            default_url="https://amazon.com/dp/B09V3KXJPB",
            slug="custom-slug",
            geo_rules=[
                {"country_code": "GB", "destination_url": "https://amazon.co.uk/dp/B09V3KXJPB"},
            ],
        )

        tool = mcp._tool_manager._tools["youfiliate_create_smart_link"]
        result = await tool.fn(params)

        assert "Smart Link Created" in result
        # Verify request body
        request = mock_api.calls[-1].request
        body = json.loads(request.content)
        assert body["slug"] == "custom-slug"
        assert len(body["geo_rules"]) == 1

    @pytest.mark.asyncio
    async def test_create_json_format(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.post(f"{BASE}/api/smart-links/").mock(
            return_value=Response(201, json=SAMPLE_SMART_LINK)
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_smart_link_tools(mcp, client)

        params = CreateSmartLinkInput(
            default_url="https://amazon.com/dp/B09V3KXJPB",
            response_format="json",
        )

        tool = mcp._tool_manager._tools["youfiliate_create_smart_link"]
        result = await tool.fn(params)

        parsed = json.loads(result)
        assert parsed["id"] == SAMPLE_SMART_LINK["id"]

    @pytest.mark.asyncio
    async def test_create_api_error(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.post(f"{BASE}/api/smart-links/").mock(
            return_value=Response(400, json={"slug": ["This slug is already taken."]})
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_smart_link_tools(mcp, client)

        params = CreateSmartLinkInput(
            default_url="https://amazon.com/dp/B09V3KXJPB",
            slug="taken-slug",
        )

        tool = mcp._tool_manager._tools["youfiliate_create_smart_link"]
        result = await tool.fn(params)

        assert "Error" in result
        assert "slug" in result.lower()


class TestListSmartLinks:
    """Tests for youfiliate_list_smart_links."""

    @pytest.mark.asyncio
    async def test_list_paginated(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.get(f"{BASE}/api/smart-links/").mock(
            return_value=Response(200, json={
                "count": 2,
                "results": [SAMPLE_SMART_LINK, {**SAMPLE_SMART_LINK, "id": "bbbbbbbb-0000-0000-0000-000000000000", "slug": "other-link"}],
            })
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_smart_link_tools(mcp, client)

        params = ListSmartLinksInput()
        tool = mcp._tool_manager._tools["youfiliate_list_smart_links"]
        result = await tool.fn(params)

        assert "Smart Links" in result
        assert "Total: 2" in result
        assert "my-test-link" in result
        assert "other-link" in result

    @pytest.mark.asyncio
    async def test_list_empty(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.get(f"{BASE}/api/smart-links/").mock(
            return_value=Response(200, json={"count": 0, "results": []})
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_smart_link_tools(mcp, client)

        params = ListSmartLinksInput()
        tool = mcp._tool_manager._tools["youfiliate_list_smart_links"]
        result = await tool.fn(params)

        assert "No smart links found" in result

    @pytest.mark.asyncio
    async def test_list_json_format(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.get(f"{BASE}/api/smart-links/").mock(
            return_value=Response(200, json={"count": 1, "results": [SAMPLE_SMART_LINK]})
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_smart_link_tools(mcp, client)

        params = ListSmartLinksInput(response_format="json")
        tool = mcp._tool_manager._tools["youfiliate_list_smart_links"]
        result = await tool.fn(params)

        parsed = json.loads(result)
        assert parsed["total"] == 1
        assert parsed["has_more"] is False


class TestGetSmartLink:
    """Tests for youfiliate_get_smart_link."""

    @pytest.mark.asyncio
    async def test_get_by_id(self, mock_api, client: YoufiliateClient) -> None:
        link_id = SAMPLE_SMART_LINK["id"]
        mock_api.get(f"{BASE}/api/smart-links/{link_id}/").mock(
            return_value=Response(200, json=SAMPLE_SMART_LINK)
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_smart_link_tools(mcp, client)

        params = GetSmartLinkInput(id=link_id)
        tool = mcp._tool_manager._tools["youfiliate_get_smart_link"]
        result = await tool.fn(params)

        assert "Smart Link Details" in result
        assert "my-test-link" in result
        assert "GB" in result  # geo rule

    @pytest.mark.asyncio
    async def test_get_not_found(self, mock_api, client: YoufiliateClient) -> None:
        not_found_id = "00000000-0000-0000-0000-000000000000"
        mock_api.get(f"{BASE}/api/smart-links/{not_found_id}/").mock(
            return_value=Response(404, json={"detail": "Not found."})
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_smart_link_tools(mcp, client)

        params = GetSmartLinkInput(id=not_found_id)
        tool = mcp._tool_manager._tools["youfiliate_get_smart_link"]
        result = await tool.fn(params)

        assert "Error" in result
        assert "not found" in result.lower()


class TestUpdateSmartLink:
    """Tests for youfiliate_update_smart_link."""

    @pytest.mark.asyncio
    async def test_update_title(self, mock_api, client: YoufiliateClient) -> None:
        link_id = SAMPLE_SMART_LINK["id"]
        updated = {**SAMPLE_SMART_LINK, "title": "Updated Title"}
        mock_api.patch(f"{BASE}/api/smart-links/{link_id}/").mock(
            return_value=Response(200, json=updated)
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_smart_link_tools(mcp, client)

        params = UpdateSmartLinkInput(id=link_id, title="Updated Title")
        tool = mcp._tool_manager._tools["youfiliate_update_smart_link"]
        result = await tool.fn(params)

        assert "Updated" in result
        assert "Updated Title" in result

    @pytest.mark.asyncio
    async def test_update_no_fields(self, mock_api, client: YoufiliateClient) -> None:
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_smart_link_tools(mcp, client)

        params = UpdateSmartLinkInput(id="00000000-0000-0000-0000-000000000000")
        tool = mcp._tool_manager._tools["youfiliate_update_smart_link"]
        result = await tool.fn(params)

        assert "Error" in result
        assert "No fields" in result


class TestDeleteSmartLink:
    """Tests for youfiliate_delete_smart_link."""

    @pytest.mark.asyncio
    async def test_delete_without_confirm(self, mock_api, client: YoufiliateClient) -> None:
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_smart_link_tools(mcp, client)

        params = DeleteSmartLinkInput(id="00000000-0000-0000-0000-000000000000", confirm=False)
        tool = mcp._tool_manager._tools["youfiliate_delete_smart_link"]
        result = await tool.fn(params)

        assert "confirmation" in result.lower() or "confirm" in result.lower()

    @pytest.mark.asyncio
    async def test_delete_with_confirm(self, mock_api, client: YoufiliateClient) -> None:
        link_id = SAMPLE_SMART_LINK["id"]
        mock_api.delete(f"{BASE}/api/smart-links/{link_id}/").mock(
            return_value=Response(204)
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_smart_link_tools(mcp, client)

        params = DeleteSmartLinkInput(id=link_id, confirm=True)
        tool = mcp._tool_manager._tools["youfiliate_delete_smart_link"]
        result = await tool.fn(params)

        assert "deleted" in result.lower()
        assert link_id in result
