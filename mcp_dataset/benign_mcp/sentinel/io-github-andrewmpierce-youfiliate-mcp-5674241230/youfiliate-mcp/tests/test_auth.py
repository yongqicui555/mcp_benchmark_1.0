"""Tests for auth manager and JWT caching."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from youfiliate_mcp.auth import AuthManager
from youfiliate_mcp.config import settings

BASE = settings.youfiliate_api_base_url


class TestAuthManager:
    @pytest.mark.asyncio
    async def test_get_access_token(self, mock_api) -> None:
        auth = AuthManager(api_key=settings.youfiliate_api_key)
        token = await auth.get_access_token()
        assert token == "test-jwt-access-token"

    @pytest.mark.asyncio
    async def test_token_caching(self, mock_api) -> None:
        auth = AuthManager(api_key=settings.youfiliate_api_key)

        # First call triggers exchange
        await auth.get_access_token()
        # Second call should use cache
        await auth.get_access_token()

        # Only one call to verify-api-key
        verify_calls = [
            c for c in mock_api.calls
            if "verify-api-key" in str(c.request.url)
        ]
        assert len(verify_calls) == 1

    @pytest.mark.asyncio
    async def test_refresh_clears_cache(self, mock_api) -> None:
        auth = AuthManager(api_key=settings.youfiliate_api_key)

        await auth.get_access_token()
        await auth.refresh()

        # Two calls: initial + refresh
        verify_calls = [
            c for c in mock_api.calls
            if "verify-api-key" in str(c.request.url)
        ]
        assert len(verify_calls) == 2

    @pytest.mark.asyncio
    async def test_api_key_change_invalidates_cache(self, mock_api) -> None:
        auth = AuthManager(api_key=settings.youfiliate_api_key)

        await auth.get_access_token()
        auth.api_key = "youfiliate_sk_newtestkey00000000000000000000"
        # Cache should be invalidated
        assert not auth._is_valid()

    @pytest.mark.asyncio
    async def test_auth_error(self) -> None:
        with respx.mock:
            respx.post(f"{BASE}/api/auth/verify-api-key/").mock(
                return_value=Response(401, json={"error": "Invalid API key"})
            )

            auth = AuthManager(api_key="youfiliate_sk_invalid00000000000000000000")
            with pytest.raises(Exception):
                await auth.get_access_token()
