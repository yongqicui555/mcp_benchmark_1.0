"""Shared test fixtures for MCP server tests."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from youfiliate_mcp.auth import AuthManager
from youfiliate_mcp.client import YoufiliateClient
from youfiliate_mcp.config import settings


# Override settings for tests
settings.youfiliate_api_base_url = "https://api.test.youfiliate.com"
settings.youfiliate_api_key = "youfiliate_sk_test0000000000000000000000000000"
settings.mcp_server_secret = ""


@pytest.fixture
def mock_api():
    """Activate respx mock for all httpx requests."""
    with respx.mock(assert_all_called=False) as mock:
        # Mock the verify-api-key endpoint (auth)
        mock.post(
            f"{settings.youfiliate_api_base_url}/api/auth/verify-api-key/"
        ).mock(
            return_value=Response(
                200,
                json={
                    "access": "test-jwt-access-token",
                    "refresh": "test-jwt-refresh-token",
                    "user_id": "00000000-0000-0000-0000-000000000001",
                },
            )
        )
        yield mock


@pytest.fixture
def auth(mock_api) -> AuthManager:
    """AuthManager with mocked token exchange."""
    return AuthManager(api_key=settings.youfiliate_api_key)


@pytest.fixture
def client(auth: AuthManager) -> YoufiliateClient:
    """YoufiliateClient with mocked auth."""
    return YoufiliateClient(auth=auth)


# Sample data fixtures

SAMPLE_SMART_LINK = {
    "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "slug": "my-test-link",
    "title": "Test Smart Link",
    "default_url": "https://amazon.com/dp/B09V3KXJPB",
    "redirect_type": "302",
    "health_status": "healthy",
    "total_clicks": 1234,
    "daily_clicks": 56,
    "weekly_clicks": 345,
    "is_active": True,
    "created_at": "2026-01-15T10:30:00Z",
    "updated_at": "2026-04-01T08:00:00Z",
    "geo_rules": [
        {"country_code": "GB", "destination_url": "https://amazon.co.uk/dp/B09V3KXJPB"},
        {"country_code": "DE", "destination_url": "https://amazon.de/dp/B09V3KXJPB"},
    ],
    "deep_link_config": {
        "ios_app_url": "amazon://dp/B09V3KXJPB",
        "ios_fallback_url": "https://amazon.com/dp/B09V3KXJPB",
        "android_app_url": "amazon://dp/B09V3KXJPB",
        "android_fallback_url": "https://amazon.com/dp/B09V3KXJPB",
    },
}

SAMPLE_STATS = {
    "period": "30d",
    "summary": {
        "total_clicks": 1234,
        "unique_visitors": 890,
    },
    "by_country": [
        {"country_code": "US", "clicks": 500},
        {"country_code": "GB", "clicks": 200},
        {"country_code": "DE", "clicks": 150},
    ],
    "by_device": [
        {"device_type": "mobile", "clicks": 700},
        {"device_type": "desktop", "clicks": 534},
    ],
    "by_referrer": [
        {"referrer": "youtube.com", "clicks": 900},
        {"referrer": "direct", "clicks": 334},
    ],
    "by_day": [
        {"date": "2026-04-01", "clicks": 45},
        {"date": "2026-04-02", "clicks": 52},
    ],
}

SAMPLE_MIGRATION = {
    "id": "11111111-2222-3333-4444-555555555555",
    "status": "completed",
    "conversion_mode": "affiliate_only",
    "auto_geo_rules": True,
    "videos_total": 10,
    "videos_processed": 10,
    "links_created": 25,
    "links_skipped": 3,
    "created_at": "2026-04-01T12:00:00Z",
    "error_message": None,
}
