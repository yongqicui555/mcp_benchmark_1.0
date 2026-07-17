"""Async HTTP client for the Minuet public API."""

from __future__ import annotations

import os
from importlib.metadata import PackageNotFoundError, version
from typing import Any

import httpx

DEFAULT_BASE_URL = "https://minuet.ai"
DEFAULT_TIMEOUT = 20.0

try:
    _VERSION = version("minuet-mcp")
except PackageNotFoundError:  # running from a source tree without install
    _VERSION = "0.0.0+local"

USER_AGENT = f"minuet-mcp/{_VERSION}"


class MinuetClient:
    """Thin async wrapper around the Minuet Flask API.

    All methods return the parsed JSON body. The API is read-only from this
    client's perspective — write routes (claim, propose, confirm) are
    wallet-gated and intentionally not exposed here.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = (base_url or os.environ.get("MINUET_API_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self._client = client
        self._owns_client = client is None
        self._headers = {"User-Agent": USER_AGENT}

    async def __aenter__(self) -> "MinuetClient":
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url, timeout=self.timeout, headers=self._headers
            )
        return self

    async def __aexit__(self, *exc: Any) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if self._client is None:
            # Allow one-shot usage without `async with`.
            async with httpx.AsyncClient(
                base_url=self.base_url, timeout=self.timeout, headers=self._headers
            ) as client:
                response = await client.get(path, params=params)
        else:
            response = await self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    # ----- Agents -----

    async def list_agents(
        self,
        name: str | None = None,
        mcp_tools: str | None = None,
        active: bool | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if name:
            params["name"] = name
        if mcp_tools:
            params["mcpTools"] = mcp_tools
        if active is not None:
            params["active"] = "true" if active else "false"
        if limit is not None:
            params["limit"] = limit
        return await self._get("/api/agents", params=params or None)

    async def get_agent(self, agent_id: str) -> dict[str, Any]:
        return await self._get(f"/api/agent/{agent_id}")

    async def get_agent_relationships(
        self, agent_id: str, direction: str = "both"
    ) -> dict[str, Any]:
        return await self._get(
            f"/api/agent/{agent_id}/relationships",
            params={"direction": direction},
        )

    # ----- Relationships -----

    async def list_relationships(self) -> dict[str, Any]:
        return await self._get("/api/relationships")

    async def get_clusters(self) -> dict[str, Any]:
        return await self._get("/api/relationships/clusters")
