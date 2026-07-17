"""Tests for per-request Bearer token auth (HTTP transport).

These cover the fix for the bug where `youfiliate-mcp.onrender.com` was
ignoring incoming `Authorization: Bearer <key>` headers and using a
single shared API key from the server's env — resulting in every request
hitting `verify-api-key` with an empty key.
"""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from youfiliate_mcp.auth import AuthManager
from youfiliate_mcp.config import settings
from youfiliate_mcp.errors import MissingAPIKeyError
from youfiliate_mcp.middleware import BearerAuthMiddleware, _extract_bearer_token
from youfiliate_mcp.request_context import current_api_key

BASE = settings.youfiliate_api_base_url


class TestBearerTokenExtraction:
    def test_extracts_bearer_token(self) -> None:
        headers = [(b"authorization", b"Bearer youfiliate_sk_abc123")]
        assert _extract_bearer_token(headers) == "youfiliate_sk_abc123"

    def test_header_name_is_case_insensitive(self) -> None:
        headers = [(b"Authorization", b"Bearer youfiliate_sk_abc123")]
        assert _extract_bearer_token(headers) == "youfiliate_sk_abc123"

    def test_scheme_is_case_insensitive(self) -> None:
        headers = [(b"authorization", b"bearer youfiliate_sk_abc123")]
        assert _extract_bearer_token(headers) == "youfiliate_sk_abc123"

    def test_strips_surrounding_whitespace(self) -> None:
        headers = [(b"authorization", b"Bearer   youfiliate_sk_abc123  ")]
        assert _extract_bearer_token(headers) == "youfiliate_sk_abc123"

    def test_returns_empty_when_absent(self) -> None:
        assert _extract_bearer_token([]) == ""

    def test_returns_empty_for_non_bearer_scheme(self) -> None:
        headers = [(b"authorization", b"Token youfiliate_sk_abc123")]
        assert _extract_bearer_token(headers) == ""


class TestBearerAuthMiddleware:
    @pytest.mark.asyncio
    async def test_sets_context_var_for_http_request(self) -> None:
        """Middleware puts the Bearer token into current_api_key for the downstream app."""
        captured: dict[str, str] = {}

        async def inner(scope, receive, send) -> None:
            captured["key"] = current_api_key.get()

        mw = BearerAuthMiddleware(inner)
        scope = {
            "type": "http",
            "headers": [(b"authorization", b"Bearer youfiliate_sk_user_one")],
        }
        await mw(scope, None, None)  # type: ignore[arg-type]
        assert captured["key"] == "youfiliate_sk_user_one"

    @pytest.mark.asyncio
    async def test_resets_context_var_after_request(self) -> None:
        """ContextVar is restored after the request, preventing leakage."""
        async def inner(scope, receive, send) -> None:
            return

        mw = BearerAuthMiddleware(inner)
        scope = {
            "type": "http",
            "headers": [(b"authorization", b"Bearer youfiliate_sk_abc")],
        }
        await mw(scope, None, None)  # type: ignore[arg-type]
        assert current_api_key.get() == ""

    @pytest.mark.asyncio
    async def test_passes_through_non_http_scope(self) -> None:
        """Lifespan/websocket scopes are forwarded without touching the ContextVar."""
        called = {"flag": False}

        async def inner(scope, receive, send) -> None:
            called["flag"] = True

        mw = BearerAuthMiddleware(inner)
        await mw({"type": "lifespan"}, None, None)  # type: ignore[arg-type]
        assert called["flag"] is True
        assert current_api_key.get() == ""

    @pytest.mark.asyncio
    async def test_missing_header_leaves_context_empty(self) -> None:
        captured: dict[str, str] = {}

        async def inner(scope, receive, send) -> None:
            captured["key"] = current_api_key.get()

        mw = BearerAuthMiddleware(inner)
        await mw({"type": "http", "headers": []}, None, None)  # type: ignore[arg-type]
        assert captured["key"] == ""


class TestAuthManagerContextVar:
    """AuthManager resolves the key from ContextVar first, falling back sanely."""

    @pytest.mark.asyncio
    async def test_context_key_takes_priority_over_instance_key(self, mock_api) -> None:
        auth = AuthManager(api_key="youfiliate_sk_instance_fallback")
        token = current_api_key.set("youfiliate_sk_context_user")
        try:
            await auth.get_access_token()
        finally:
            current_api_key.reset(token)

        verify_calls = [
            c for c in mock_api.calls if "verify-api-key" in str(c.request.url)
        ]
        assert len(verify_calls) == 1
        # The context key, not the instance key, is what hit the API.
        body = verify_calls[0].request.content.decode()
        assert "youfiliate_sk_context_user" in body
        assert "youfiliate_sk_instance_fallback" not in body

    @pytest.mark.asyncio
    async def test_tokens_cached_per_key(self, mock_api) -> None:
        """Two different users share an AuthManager but each gets their own token."""
        auth = AuthManager()

        token_a = current_api_key.set("youfiliate_sk_user_a")
        try:
            await auth.get_access_token()
            await auth.get_access_token()  # cached
        finally:
            current_api_key.reset(token_a)

        token_b = current_api_key.set("youfiliate_sk_user_b")
        try:
            await auth.get_access_token()  # fresh exchange for user B
            await auth.get_access_token()  # cached
        finally:
            current_api_key.reset(token_b)

        # Back to user A — should still be cached, no extra exchange.
        token_a2 = current_api_key.set("youfiliate_sk_user_a")
        try:
            await auth.get_access_token()
        finally:
            current_api_key.reset(token_a2)

        verify_calls = [
            c for c in mock_api.calls if "verify-api-key" in str(c.request.url)
        ]
        # One exchange per distinct key — 2 total, not 5.
        assert len(verify_calls) == 2

    @pytest.mark.asyncio
    async def test_missing_key_raises(self) -> None:
        """With no ContextVar, no instance key, and no env var, exchange fails clearly."""
        original = settings.youfiliate_api_key
        settings.youfiliate_api_key = ""
        try:
            auth = AuthManager()
            with pytest.raises(MissingAPIKeyError):
                await auth.get_access_token()
        finally:
            settings.youfiliate_api_key = original

    @pytest.mark.asyncio
    async def test_falls_back_to_env_in_stdio_mode(self, mock_api) -> None:
        """Without a per-request key, settings.youfiliate_api_key is used."""
        auth = AuthManager()  # no instance key
        # ContextVar is empty by default.
        await auth.get_access_token()

        verify_calls = [
            c for c in mock_api.calls if "verify-api-key" in str(c.request.url)
        ]
        assert len(verify_calls) == 1
        body = verify_calls[0].request.content.decode()
        assert settings.youfiliate_api_key in body
