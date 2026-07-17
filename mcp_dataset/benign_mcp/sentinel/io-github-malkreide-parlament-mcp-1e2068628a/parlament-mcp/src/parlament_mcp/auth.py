"""Session-Binding & optionale Bearer-Authentifizierung (SEC-009).

Für Streamable HTTP. Bindet die ``Mcp-Session-Id`` kryptografisch an eine
**validierte** Identität, sodass eine geleakte/erratene Session-ID nicht
genügt, um im Kontext eines anderen Users zu agieren.

Auth ist **opt-in**: ohne konfigurierte Tokens (``MCP_BEARER_TOKENS``) läuft der
Server wie bisher offen (Public Open Data). Sobald Tokens gesetzt sind, wird auf
dem HTTP-Transport ein gültiges ``Authorization: Bearer``-Token verlangt und die
Session daran gebunden.

Stdlib-only (hmac/secrets) — keine zusätzliche Dependency.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time

SESSION_TTL_SECONDS = 3600  # 1h
_SESSION_ID_BYTES = 32  # 256 Bit Entropie


class AuthError(Exception):
    """Authentifizierung/Session-Validierung fehlgeschlagen."""


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def load_bearer_tokens() -> dict[str, str]:
    """Konfigurierte Bearer-Tokens aus ``MCP_BEARER_TOKENS`` laden.

    Format: ``user_id:token`` kommasepariert, z.B.
    ``MCP_BEARER_TOKENS="alice:tok_abc,bob:tok_def"``. Leere Map → Auth aus.
    Mapping: token → user_id.
    """
    raw = os.environ.get("MCP_BEARER_TOKENS", "").strip()
    tokens: dict[str, str] = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if not pair or ":" not in pair:
            continue
        user_id, token = pair.split(":", 1)
        if user_id.strip() and token.strip():
            tokens[token.strip()] = user_id.strip()
    return tokens


def auth_enabled() -> bool:
    return bool(load_bearer_tokens())


def verify_bearer(token: str) -> str:
    """Bearer-Token → user_id. Wirft ``AuthError`` bei Ungültigkeit."""
    user_id = load_bearer_tokens().get(token)
    if user_id is None:
        raise AuthError("Ungültiges Bearer-Token")
    return user_id


def new_session_id() -> str:
    """Kryptografisch sichere Session-ID (256 Bit, URL-safe)."""
    return secrets.token_urlsafe(_SESSION_ID_BYTES)


class SessionSigner:
    """Signiert/validiert an ``user_id`` gebundene Session-Tokens (HMAC-SHA256)."""

    def __init__(self, secret: str | None = None, ttl: int = SESSION_TTL_SECONDS) -> None:
        self._secret = (secret or os.environ.get("MCP_SESSION_SECRET") or "").encode("utf-8")
        if not self._secret:
            # Ephemeres Secret: Tokens überleben keinen Neustart (bewusst,
            # für Single-Instance ok; produktiv MCP_SESSION_SECRET setzen).
            self._secret = secrets.token_bytes(32)
        self._ttl = ttl
        self._revoked: set[str] = set()

    def _sign(self, payload: str) -> str:
        return _b64e(hmac.new(self._secret, payload.encode("utf-8"), hashlib.sha256).digest())

    def create(self, user_id: str, session_id: str | None = None) -> str:
        """Signiertes, an ``user_id`` gebundenes Session-Token erzeugen."""
        session_id = session_id or new_session_id()
        expiry = int(time.time()) + self._ttl
        payload = f"{user_id}:{session_id}:{expiry}"
        return f"{_b64e(payload.encode('utf-8'))}.{self._sign(payload)}"

    def validate(self, token: str, claimed_user_id: str) -> dict:
        """Token gegen Signatur, Ablauf und User-Bindung prüfen."""
        try:
            body_b64, sig = token.split(".", 1)
            payload = _b64d(body_b64).decode("utf-8")
        except Exception as exc:  # noqa: BLE001
            raise AuthError("Malformed session token") from exc

        if not hmac.compare_digest(sig, self._sign(payload)):
            raise AuthError("Ungültige Session-Signatur")

        try:
            user_id, session_id, expiry_s = payload.rsplit(":", 2)
            expiry = int(expiry_s)
        except ValueError as exc:
            raise AuthError("Malformed session payload") from exc

        if time.time() > expiry:
            raise AuthError("Session abgelaufen")
        if user_id != claimed_user_id:
            raise AuthError("Session gehört nicht zu diesem User")
        if token in self._revoked:
            raise AuthError("Session widerrufen")
        return {"user_id": user_id, "session_id": session_id, "expiry": expiry}

    def revoke(self, token: str) -> None:
        """Session serverseitig invalidieren (Logout)."""
        self._revoked.add(token)


def build_bearer_middleware():
    """Starlette-Middleware-Klasse: erzwingt – sofern Auth aktiv – ein gültiges
    ``Authorization: Bearer``-Token **pro Request**.

    Damit kommt die User-Identität aus dem validierten Token, nicht aus einem
    Client-/Session-Header — ein erratenes/geleaktes ``Mcp-Session-Id`` genügt
    nicht, um im Kontext eines anderen Users zu agieren (SEC-009). Ohne
    konfigurierte Tokens ist die Middleware ein No-op (Public-Open-Data-Default).
    """
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import JSONResponse

    class BearerAuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            if not auth_enabled():
                return await call_next(request)
            header = request.headers.get("Authorization", "")
            if not header.startswith("Bearer "):
                return JSONResponse({"error": "Bearer token required"}, status_code=401)
            try:
                user_id = verify_bearer(header[len("Bearer ") :].strip())
            except AuthError:
                return JSONResponse({"error": "Invalid bearer token"}, status_code=401)
            # Validierte Identität pro Request — nicht aus Session-Header abgeleitet.
            request.state.user_id = user_id
            return await call_next(request)

    return BearerAuthMiddleware
