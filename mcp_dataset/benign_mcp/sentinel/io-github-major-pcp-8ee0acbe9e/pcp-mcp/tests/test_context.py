"""Tests for context helper functions."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp import Context
from fastmcp.exceptions import ToolError

from pcp_mcp.context import get_client, get_client_for_host, get_settings


class TestGetClient:
    def test_returns_client_from_valid_context(self, mock_context: MagicMock) -> None:
        client = get_client(mock_context)
        assert client is mock_context.request_context.lifespan_context["client"]

    def test_raises_tool_error_when_request_context_is_none(self) -> None:
        ctx = MagicMock(spec=Context)
        ctx.request_context = None

        with pytest.raises(ToolError, match="Server context not available"):
            get_client(ctx)

    def test_raises_tool_error_when_lifespan_context_is_none(self) -> None:
        ctx = MagicMock(spec=Context)
        ctx.request_context = MagicMock()
        ctx.request_context.lifespan_context = None

        with pytest.raises(ToolError, match="Server context not available"):
            get_client(ctx)


class TestGetSettings:
    def test_returns_settings_from_valid_context(self, mock_context: MagicMock) -> None:
        settings = get_settings(mock_context)
        assert settings is mock_context.request_context.lifespan_context["settings"]

    def test_raises_tool_error_when_request_context_is_none(self) -> None:
        ctx = MagicMock(spec=Context)
        ctx.request_context = None

        with pytest.raises(ToolError, match="Server context not available"):
            get_settings(ctx)

    def test_raises_tool_error_when_lifespan_context_is_none(self) -> None:
        ctx = MagicMock(spec=Context)
        ctx.request_context = MagicMock()
        ctx.request_context.lifespan_context = None

        with pytest.raises(ToolError, match="Server context not available"):
            get_settings(ctx)


class TestGetClientForHost:
    async def test_returns_default_client_when_host_is_none(self, mock_context: MagicMock) -> None:
        async with get_client_for_host(mock_context, host=None) as client:
            assert client is mock_context.request_context.lifespan_context["client"]

    async def test_returns_default_client_when_host_matches_target(
        self, mock_context: MagicMock
    ) -> None:
        async with get_client_for_host(mock_context, host="localhost") as client:
            assert client is mock_context.request_context.lifespan_context["client"]

    async def test_creates_new_client_for_different_host(self, mock_context: MagicMock) -> None:
        mock_context.request_context.lifespan_context["settings"].allowed_hosts = [
            "remote.example.com"
        ]

        mock_client_instance = AsyncMock()
        mock_client_instance.target_host = "remote.example.com"
        mock_client_instance.__aenter__.return_value = mock_client_instance

        with patch("pcp_mcp.context.PCPClient") as mock_pcp_client:
            mock_pcp_client.return_value = mock_client_instance

            async with get_client_for_host(mock_context, host="remote.example.com") as client:
                assert client is mock_client_instance
                mock_client_instance.__aenter__.assert_called_once()

            mock_client_instance.__aexit__.assert_called_once()

    async def test_new_client_uses_settings_from_context(self, mock_context: MagicMock) -> None:
        mock_client_instance = AsyncMock()
        settings = mock_context.request_context.lifespan_context["settings"]
        settings.allowed_hosts = ["remote.example.com"]

        with patch("pcp_mcp.context.PCPClient") as mock_pcp_client:
            mock_pcp_client.return_value = mock_client_instance

            async with get_client_for_host(mock_context, host="remote.example.com") as _:
                mock_pcp_client.assert_called_once_with(
                    base_url=settings.base_url,
                    target_host="remote.example.com",
                    auth=settings.auth,
                    timeout=settings.timeout,
                    verify=settings.verify,
                )

    async def test_aenter_failure_propagates(self, mock_context: MagicMock) -> None:
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.side_effect = ConnectionError("Connection refused")

        mock_context.request_context.lifespan_context["settings"].allowed_hosts = ["*"]

        with patch("pcp_mcp.context.PCPClient") as mock_pcp_client:
            mock_pcp_client.return_value = mock_client_instance

            with pytest.raises(ConnectionError, match="Connection refused"):
                async with get_client_for_host(mock_context, host="unreachable.example.com"):
                    pass

    async def test_rejects_host_not_in_allowlist(self, mock_context: MagicMock) -> None:
        with pytest.raises(ToolError, match="not in the allowed hosts list"):
            async with get_client_for_host(mock_context, host="attacker.example.com"):
                pass

    @pytest.mark.parametrize(
        ("allowed_hosts", "query_host"),
        [
            (["permitted.example.com"], "permitted.example.com"),
            (["*"], "any.host.com"),
        ],
        ids=["explicit_allowlist", "wildcard"],
    )
    async def test_allows_host_when_in_allowlist(
        self, mock_context: MagicMock, allowed_hosts: list[str], query_host: str
    ) -> None:
        mock_context.request_context.lifespan_context["settings"].allowed_hosts = allowed_hosts

        mock_client_instance = AsyncMock()
        mock_client_instance.target_host = query_host
        mock_client_instance.__aenter__.return_value = mock_client_instance

        with patch("pcp_mcp.context.PCPClient") as mock_pcp_client:
            mock_pcp_client.return_value = mock_client_instance

            async with get_client_for_host(mock_context, host=query_host) as client:
                assert client is mock_client_instance
