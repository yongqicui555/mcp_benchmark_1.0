"""Auth manager: exchanges Youfiliate API keys for JWTs, with per-key caching.

The server shares a single `AuthManager` instance across all requests. The
effective API key for any given call is resolved in priority order:

  1. Per-request key from `current_api_key` ContextVar (HTTP transport —
     set by `BearerAuthMiddleware` from `Authorization: Bearer <key>`).
  2. Instance-level key passed to the constructor (used by tests).
  3. `YOUFILIATE_API_KEY` env var (stdio transport).

JWT tokens are cached in a per-instance dict keyed by the API key, so
concurrent users on the HTTP transport each get their own cached token.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import httpx

from .config import settings
from .errors import MissingAPIKeyError
from .request_context import current_api_key


@dataclass
class CachedToken:
    """A cached JWT access/refresh token pair."""
    access: str
    refresh: str
    obtained_at: float = field(default_factory=time.monotonic)
    # DRF default: 1 hour access, 7 day refresh
    access_lifetime: int = 3500  # refresh a bit before expiry


class AuthManager:
    """Manages API key -> JWT exchange with per-key caching.

    On each API call the current effective key is resolved from the
    ContextVar / instance / env fallback chain, and its cached JWT is
    returned if still valid. Otherwise a fresh exchange is performed and
    the new token is cached under that key.

    On a 401 response during an API call, the client calls `refresh()`
    which invalidates the cached token for the current key and forces a
    new exchange on the next call.
    """

    def __init__(self, api_key: str = "") -> None:
        self._instance_api_key = api_key
        self._cache: dict[str, CachedToken] = {}

    @property
    def api_key(self) -> str:
        """Resolve the effective API key for the current request."""
        ctx_key = current_api_key.get()
        if ctx_key:
            return ctx_key
        if self._instance_api_key:
            return self._instance_api_key
        return settings.youfiliate_api_key

    @api_key.setter
    def api_key(self, value: str) -> None:
        """Change the instance-level key and drop its cached token."""
        self._cache.pop(self._instance_api_key, None)
        self._instance_api_key = value

    def _is_valid(self) -> bool:
        """Check if the cached token for the current key is still valid."""
        key = self.api_key
        cached = self._cache.get(key)
        if cached is None:
            return False
        elapsed = time.monotonic() - cached.obtained_at
        return elapsed < cached.access_lifetime

    async def get_access_token(self) -> str:
        """Return a valid JWT access token for the current request's API key."""
        if self._is_valid():
            return self._cache[self.api_key].access
        await self._exchange_key()
        return self._cache[self.api_key].access

    async def refresh(self) -> str:
        """Force a new JWT exchange for the current key (called on 401)."""
        self._cache.pop(self.api_key, None)
        return await self.get_access_token()

    async def _exchange_key(self) -> None:
        """Call the DRF verify-api-key endpoint to get a JWT pair."""
        key = self.api_key
        if not key:
            raise MissingAPIKeyError(
                "No Youfiliate API key available for this request."
            )

        url = f"{settings.youfiliate_api_base_url}/api/auth/verify-api-key/"
        headers: dict[str, str] = {}
        if settings.mcp_server_secret:
            headers["X-MCP-Server-Secret"] = settings.mcp_server_secret

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json={"key": key},
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

        self._cache[key] = CachedToken(
            access=data["access"],
            refresh=data["refresh"],
        )
