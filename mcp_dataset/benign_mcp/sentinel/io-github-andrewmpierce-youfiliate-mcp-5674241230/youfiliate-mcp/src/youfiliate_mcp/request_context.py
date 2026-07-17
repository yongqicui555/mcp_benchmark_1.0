"""Per-request context for HTTP transport.

When running under the `streamable-http` transport, each incoming request
may carry a different user's API key via `Authorization: Bearer <key>`.
The `BearerAuthMiddleware` stores the extracted key in the `current_api_key`
ContextVar before invoking the downstream MCP handler. The shared
`AuthManager` reads the ContextVar to select the right key per request.

Under the `stdio` transport this ContextVar stays empty, and the
`AuthManager` falls back to the process-level `YOUFILIATE_API_KEY` env var.
"""

from __future__ import annotations

from contextvars import ContextVar

# Empty string means "no per-request key" — AuthManager will fall back to
# its instance-level key (tests) or the env var (stdio mode).
current_api_key: ContextVar[str] = ContextVar("current_api_key", default="")
