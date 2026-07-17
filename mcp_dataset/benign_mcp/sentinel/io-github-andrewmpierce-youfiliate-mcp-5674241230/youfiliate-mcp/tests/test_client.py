"""Tests for the HTTP client."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from youfiliate_mcp.client import YoufiliateClient, make_api_call
from youfiliate_mcp.config import settings

BASE = settings.youfiliate_api_base_url


class TestYoufiliateClient:
    @pytest.mark.asyncio
    async def test_get_request(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.get(f"{BASE}/api/smart-links/").mock(
            return_value=Response(200, json={"results": []})
        )

        result = await client.get("/api/smart-links/")
        assert result == {"results": []}

    @pytest.mark.asyncio
    async def test_post_request(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.post(f"{BASE}/api/smart-links/").mock(
            return_value=Response(201, json={"id": "test-id"})
        )

        result = await client.post("/api/smart-links/", json={"default_url": "https://example.com"})
        assert result["id"] == "test-id"

    @pytest.mark.asyncio
    async def test_delete_returns_empty(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.delete(f"{BASE}/api/smart-links/test-id/").mock(
            return_value=Response(204)
        )

        result = await client.delete("/api/smart-links/test-id/")
        assert result == {}

    @pytest.mark.asyncio
    async def test_auto_retry_on_401(self, mock_api, client: YoufiliateClient) -> None:
        """On 401, the client refreshes the token and retries once."""
        # First call returns 401, retry returns 200
        mock_api.get(f"{BASE}/api/smart-links/").mock(
            side_effect=[
                Response(401, json={"detail": "Token expired"}),
                Response(200, json={"results": ["ok"]}),
            ]
        )

        result = await client.get("/api/smart-links/")
        assert result == {"results": ["ok"]}

    @pytest.mark.asyncio
    async def test_clean_params_removes_none(self, client: YoufiliateClient) -> None:
        cleaned = client._clean_params({"a": 1, "b": None, "c": "hello"})
        assert cleaned == {"a": 1, "c": "hello"}

    @pytest.mark.asyncio
    async def test_clean_params_none_input(self, client: YoufiliateClient) -> None:
        assert client._clean_params(None) is None


class TestMakeApiCall:
    @pytest.mark.asyncio
    async def test_success(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.get(f"{BASE}/api/smart-links/").mock(
            return_value=Response(200, json={"results": []})
        )

        ok, result = await make_api_call(client, "GET", "/api/smart-links/")
        assert ok is True
        assert result == {"results": []}

    @pytest.mark.asyncio
    async def test_http_error(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.get(f"{BASE}/api/smart-links/bad-id/").mock(
            return_value=Response(404, json={"detail": "Not found."})
        )

        ok, result = await make_api_call(client, "GET", "/api/smart-links/bad-id/")
        assert ok is False
        assert "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_server_error(self, mock_api, client: YoufiliateClient) -> None:
        mock_api.get(f"{BASE}/api/smart-links/").mock(
            return_value=Response(500, text="Internal Server Error")
        )

        ok, result = await make_api_call(client, "GET", "/api/smart-links/")
        assert ok is False
        assert "unavailable" in result.lower()
