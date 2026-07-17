"""Security tests for the MCP server."""

from __future__ import annotations

import pytest
import respx
from httpx import Response
from pydantic import ValidationError

from youfiliate_mcp.auth import AuthManager
from youfiliate_mcp.client import YoufiliateClient, make_api_call
from youfiliate_mcp.config import settings
from youfiliate_mcp.schemas.smart_links import (
    CreateSmartLinkInput,
    DeleteSmartLinkInput,
)
from youfiliate_mcp.schemas.migrations import (
    RollbackMigrationInput,
    StartMigrationInput,
)
from youfiliate_mcp.schemas.youtube import DisconnectYouTubeInput

BASE = settings.youfiliate_api_base_url


class TestInvalidAPIKeys:
    """Test that invalid API keys are rejected."""

    @pytest.mark.asyncio
    async def test_empty_api_key(self) -> None:
        with respx.mock:
            respx.post(f"{BASE}/api/auth/verify-api-key/").mock(
                return_value=Response(400, json={"error": "Invalid format"})
            )
            auth = AuthManager(api_key="")
            with pytest.raises(Exception):
                await auth.get_access_token()

    @pytest.mark.asyncio
    async def test_revoked_key(self) -> None:
        with respx.mock:
            respx.post(f"{BASE}/api/auth/verify-api-key/").mock(
                return_value=Response(401, json={"error": "Invalid or revoked API key."})
            )
            auth = AuthManager(api_key="youfiliate_sk_revoked0000000000000000000000")
            with pytest.raises(Exception):
                await auth.get_access_token()


class TestExpiredJWTHandling:
    """Test that expired JWTs trigger re-auth."""

    @pytest.mark.asyncio
    async def test_401_triggers_refresh(self, mock_api, client: YoufiliateClient) -> None:
        """After a 401, client should refresh and retry."""
        mock_api.get(f"{BASE}/api/smart-links/").mock(
            side_effect=[
                Response(401, json={"detail": "Token expired"}),
                Response(200, json={"results": []}),
            ]
        )

        ok, result = await make_api_call(client, "GET", "/api/smart-links/")
        assert ok is True


class TestDestructiveActionConfirmation:
    """Test that destructive actions require confirm=True."""

    def test_delete_defaults_to_no_confirm(self) -> None:
        params = DeleteSmartLinkInput(id="00000000-0000-0000-0000-000000000000")
        assert params.confirm is False

    def test_start_migration_defaults_to_no_confirm(self) -> None:
        params = StartMigrationInput()
        assert params.confirm is False

    def test_rollback_defaults_to_no_confirm(self) -> None:
        params = RollbackMigrationInput(id="00000000-0000-0000-0000-000000000000")
        assert params.confirm is False

    def test_disconnect_youtube_defaults_to_no_confirm(self) -> None:
        params = DisconnectYouTubeInput()
        assert params.confirm is False


class TestMalformedInputs:
    """Test that malformed inputs are rejected by Pydantic."""

    def test_oversized_title(self) -> None:
        with pytest.raises(ValidationError):
            CreateSmartLinkInput(
                default_url="https://amazon.com",
                title="x" * 201,
            )

    def test_slug_with_special_chars(self) -> None:
        with pytest.raises(ValidationError):
            CreateSmartLinkInput(
                default_url="https://amazon.com",
                slug="my_link!@#",
            )

    def test_slug_with_unicode(self) -> None:
        with pytest.raises(ValidationError):
            CreateSmartLinkInput(
                default_url="https://amazon.com",
                slug="my-link-\u00e9",
            )

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            CreateSmartLinkInput(
                default_url="https://amazon.com",
                malicious_field="DROP TABLE;",
            )

    def test_injection_in_search(self) -> None:
        """SQL injection in search field — should pass Pydantic but be harmless
        since the DRF backend uses parameterized queries."""
        from youfiliate_mcp.schemas.smart_links import ListSmartLinksInput
        params = ListSmartLinksInput(search="'; DROP TABLE smart_links; --")
        assert params.search == "'; DROP TABLE smart_links; --"

    def test_negative_limit(self) -> None:
        from youfiliate_mcp.schemas.smart_links import ListSmartLinksInput
        with pytest.raises(ValidationError):
            ListSmartLinksInput(limit=-1)

    def test_huge_offset(self) -> None:
        """Large offset is valid — just returns empty results."""
        from youfiliate_mcp.schemas.smart_links import ListSmartLinksInput
        params = ListSmartLinksInput(offset=999999)
        assert params.offset == 999999
