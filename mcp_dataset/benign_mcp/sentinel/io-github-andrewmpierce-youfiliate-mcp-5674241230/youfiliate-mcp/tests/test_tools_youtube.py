"""Tests for YouTube and migration tools."""

from __future__ import annotations

import json

import pytest
import respx
from httpx import Response

from youfiliate_mcp.client import YoufiliateClient
from youfiliate_mcp.config import settings
from youfiliate_mcp.schemas.migrations import (
    GetMigrationStatusInput,
    ListMigrationsInput,
    PreviewMigrationInput,
    RollbackMigrationInput,
    StartMigrationInput,
)
from youfiliate_mcp.schemas.youtube import (
    ConnectYouTubeInput,
    DisconnectYouTubeInput,
    GetYouTubeStatusInput,
)
from youfiliate_mcp.tools.migrations import register_migration_tools
from youfiliate_mcp.tools.youtube import register_youtube_tools

from .conftest import SAMPLE_MIGRATION

BASE = settings.youfiliate_api_base_url


class TestYouTubeStatus:
    @pytest.mark.asyncio
    async def test_connected(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.get(f"{BASE}/api/smart-links/youtube-oauth/").mock(
            return_value=Response(200, json={
                "connected": True,
                "channel_name": "TechReviewer",
                "channel_id": "UC123",
                "scopes": ["youtube.readonly", "youtube.force-ssl"],
                "token_expiry": "2026-04-10T12:00:00Z",
            })
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_youtube_tools(mcp, client)

        params = GetYouTubeStatusInput()
        tool = mcp._tool_manager._tools["youfiliate_get_youtube_status"]
        result = await tool.fn(params)

        assert "Connected" in result
        assert "TechReviewer" in result

    @pytest.mark.asyncio
    async def test_not_connected(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.get(f"{BASE}/api/smart-links/youtube-oauth/").mock(
            return_value=Response(200, json={"connected": False})
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_youtube_tools(mcp, client)

        params = GetYouTubeStatusInput()
        tool = mcp._tool_manager._tools["youfiliate_get_youtube_status"]
        result = await tool.fn(params)

        assert "Not connected" in result


class TestConnectYouTube:
    @pytest.mark.asyncio
    async def test_connect(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.post(f"{BASE}/api/smart-links/youtube-oauth/connect/").mock(
            return_value=Response(200, json={
                "auth_url": "https://accounts.google.com/o/oauth2/auth?client_id=..."
            })
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_youtube_tools(mcp, client)

        params = ConnectYouTubeInput()
        tool = mcp._tool_manager._tools["youfiliate_connect_youtube"]
        result = await tool.fn(params)

        assert "accounts.google.com" in result
        assert "browser" in result.lower()


class TestDisconnectYouTube:
    @pytest.mark.asyncio
    async def test_disconnect_without_confirm(self, mock_api, client: YoufiliateClient) -> None:
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_youtube_tools(mcp, client)

        params = DisconnectYouTubeInput(confirm=False)
        tool = mcp._tool_manager._tools["youfiliate_disconnect_youtube"]
        result = await tool.fn(params)

        assert "confirm" in result.lower()

    @pytest.mark.asyncio
    async def test_disconnect_confirmed(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.delete(f"{BASE}/api/smart-links/youtube-oauth/disconnect/").mock(
            return_value=Response(204)
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_youtube_tools(mcp, client)

        params = DisconnectYouTubeInput(confirm=True)
        tool = mcp._tool_manager._tools["youfiliate_disconnect_youtube"]
        result = await tool.fn(params)

        assert "disconnected" in result.lower()


class TestPreviewMigration:
    @pytest.mark.asyncio
    async def test_preview(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.post(f"{BASE}/api/smart-links/migrations/preview/").mock(
            return_value=Response(200, json={
                "videos_count": 15,
                "links_count": 42,
                "conversion_mode": "affiliate_only",
                "auto_geo_rules": True,
                "videos": [
                    {"title": "Best Headphones 2026", "links_count": 5},
                    {"title": "Camera Review", "links_count": 3},
                ],
            })
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_migration_tools(mcp, client)

        params = PreviewMigrationInput()
        tool = mcp._tool_manager._tools["youfiliate_preview_migration"]
        result = await tool.fn(params)

        assert "Preview" in result
        assert "15" in result
        assert "42" in result
        assert "Best Headphones" in result


class TestStartMigration:
    @pytest.mark.asyncio
    async def test_start_without_confirm(self, mock_api, client: YoufiliateClient) -> None:
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_migration_tools(mcp, client)

        params = StartMigrationInput(confirm=False)
        tool = mcp._tool_manager._tools["youfiliate_start_migration"]
        result = await tool.fn(params)

        assert "confirm" in result.lower()
        assert "preview" in result.lower()

    @pytest.mark.asyncio
    async def test_start_confirmed(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.post(f"{BASE}/api/smart-links/migrations/").mock(
            return_value=Response(201, json=SAMPLE_MIGRATION)
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_migration_tools(mcp, client)

        params = StartMigrationInput(confirm=True)
        tool = mcp._tool_manager._tools["youfiliate_start_migration"]
        result = await tool.fn(params)

        assert "Started" in result
        assert SAMPLE_MIGRATION["id"][:8] in result


class TestGetMigrationStatus:
    @pytest.mark.asyncio
    async def test_get_status(self, mock_api, client: YoufiliateClient) -> None:
        mid = SAMPLE_MIGRATION["id"]
        mock_api.get(f"{BASE}/api/smart-links/migrations/{mid}/").mock(
            return_value=Response(200, json=SAMPLE_MIGRATION)
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_migration_tools(mcp, client)

        params = GetMigrationStatusInput(id=mid)
        tool = mcp._tool_manager._tools["youfiliate_get_migration_status"]
        result = await tool.fn(params)

        assert "completed" in result
        assert "10" in result  # videos processed


class TestListMigrations:
    @pytest.mark.asyncio
    async def test_list(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.get(f"{BASE}/api/smart-links/migrations/").mock(
            return_value=Response(200, json={
                "count": 1,
                "results": [SAMPLE_MIGRATION],
            })
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_migration_tools(mcp, client)

        params = ListMigrationsInput()
        tool = mcp._tool_manager._tools["youfiliate_list_migrations"]
        result = await tool.fn(params)

        assert "Migrations" in result
        assert "Total: 1" in result


class TestRollbackMigration:
    @pytest.mark.asyncio
    async def test_rollback_without_confirm(self, mock_api, client: YoufiliateClient) -> None:
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_migration_tools(mcp, client)

        params = RollbackMigrationInput(id="00000000-0000-0000-0000-000000000000", confirm=False)
        tool = mcp._tool_manager._tools["youfiliate_rollback_migration"]
        result = await tool.fn(params)

        assert "confirm" in result.lower()

    @pytest.mark.asyncio
    async def test_rollback_confirmed(self, mock_api, client: YoufiliateClient) -> None:
        mid = SAMPLE_MIGRATION["id"]
        mock_api.post(f"{BASE}/api/smart-links/migrations/{mid}/rollback/").mock(
            return_value=Response(200, json={"status": "rolling_back"})
        )

        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test")
        register_migration_tools(mcp, client)

        params = RollbackMigrationInput(id=mid, confirm=True)
        tool = mcp._tool_manager._tools["youfiliate_rollback_migration"]
        result = await tool.fn(params)

        assert "Rollback Started" in result
