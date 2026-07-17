"""Async HTTP client for the Youfiliate DRF API.

All tools use this client. It handles JWT injection, error parsing,
and auto-retry on 401 (token refresh).
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any

import httpx

from .auth import AuthManager
from .config import settings
from .errors import MissingAPIKeyError, handle_http_error, handle_request_error


class RateLimitExceeded(Exception):
    """Raised when the per-key rate limit is exceeded."""


class _SlidingWindowRateLimiter:
    """Simple in-memory sliding-window rate limiter."""

    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        self._max = max_requests
        self._window = window_seconds
        self._timestamps: deque[float] = deque()

    def check(self) -> None:
        """Raise RateLimitExceeded if the limit has been reached."""
        now = time.monotonic()
        cutoff = now - self._window
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()
        if len(self._timestamps) >= self._max:
            raise RateLimitExceeded(
                f"Rate limit exceeded: {self._max} requests per {self._window}s. "
                "Please wait before retrying."
            )
        self._timestamps.append(now)


class YoufiliateClient:
    """Async HTTP wrapper for the DRF API."""

    def __init__(self, auth: AuthManager | None = None) -> None:
        self.auth = auth or AuthManager()
        self.base_url = settings.youfiliate_api_base_url.rstrip("/")
        self._rate_limiter = _SlidingWindowRateLimiter(
            max_requests=settings.rate_limit_rpm, window_seconds=60,
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        retry_on_401: bool = True,
    ) -> dict[str, Any] | list[Any]:
        """Make an authenticated request to the DRF API.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses (after retry).
        """
        self._rate_limiter.check()
        token = await self.auth.get_access_token()
        url = f"{self.base_url}{path}"
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient(timeout=30.0) as http:
            response = await http.request(
                method,
                url,
                json=json,
                params=self._clean_params(params),
                headers=headers,
            )

            # Auto-refresh on 401 and retry once
            if response.status_code == 401 and retry_on_401:
                token = await self.auth.refresh()
                headers["Authorization"] = f"Bearer {token}"
                response = await http.request(
                    method,
                    url,
                    json=json,
                    params=self._clean_params(params),
                    headers=headers,
                )

            response.raise_for_status()

            # DELETE returns 204 with no body
            if response.status_code == 204:
                return {}

            return response.json()

    async def get(self, path: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
        return await self.request("POST", path, **kwargs)

    async def patch(self, path: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
        return await self.request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
        return await self.request("DELETE", path, **kwargs)

    @staticmethod
    def _clean_params(params: dict[str, Any] | None) -> dict[str, Any] | None:
        """Remove None values from query params."""
        if params is None:
            return None
        return {k: v for k, v in params.items() if v is not None}

    def safe_request(self):
        """Context manager style — not needed since we use per-request clients."""
        pass


async def make_api_call(
    client: YoufiliateClient,
    method: str,
    path: str,
    **kwargs: Any,
) -> tuple[bool, Any]:
    """Wrapper that catches errors and returns (success, result_or_error_string).

    Returns:
        (True, response_data) on success
        (False, error_message_string) on failure
    """
    try:
        result = await client.request(method, path, **kwargs)
        return True, result
    except MissingAPIKeyError as exc:
        return False, handle_request_error(exc)
    except RateLimitExceeded as exc:
        return False, str(exc)
    except httpx.HTTPStatusError as exc:
        return False, handle_http_error(exc)
    except Exception as exc:
        return False, handle_request_error(exc)
