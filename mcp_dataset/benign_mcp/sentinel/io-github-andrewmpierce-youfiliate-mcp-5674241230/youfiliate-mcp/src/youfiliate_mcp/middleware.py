"""ASGI middleware for the streamable-http transport.

`BearerAuthMiddleware` reads `Authorization: Bearer <api_key>` from each
incoming HTTP request and stores the key in `current_api_key` for the
duration of that request. Tools then pick it up via `AuthManager`.
"""

from __future__ import annotations

from starlette.types import ASGIApp, Receive, Scope, Send

from .request_context import current_api_key


class BearerAuthMiddleware:
    """Extract `Authorization: Bearer <key>` into the current_api_key ContextVar.

    Non-HTTP scopes (lifespan, websocket) are passed through unchanged.
    Requests without an Authorization header are still forwarded — the tool
    layer will surface a clear "authentication required" error if neither
    a header nor an env-var fallback is available.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        api_key = _extract_bearer_token(scope.get("headers", []))
        token = current_api_key.set(api_key)
        try:
            await self.app(scope, receive, send)
        finally:
            current_api_key.reset(token)


def _extract_bearer_token(headers: list[tuple[bytes, bytes]]) -> str:
    """Return the Bearer token from an ASGI headers list, or '' if absent."""
    for name, value in headers:
        if name.lower() == b"authorization":
            try:
                decoded = value.decode("latin-1")
            except UnicodeDecodeError:
                return ""
            # Case-insensitive scheme match; tolerate extra whitespace.
            scheme, _, token = decoded.partition(" ")
            if scheme.lower() == "bearer":
                return token.strip()
            return ""
    return ""
