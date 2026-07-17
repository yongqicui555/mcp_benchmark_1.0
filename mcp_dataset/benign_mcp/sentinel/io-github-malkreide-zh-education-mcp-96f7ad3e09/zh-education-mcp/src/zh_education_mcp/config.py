"""Laufzeit-Konfiguration (ENV-basiert) für zh-education-mcp."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Laufzeit-Konfiguration aus Umgebungsvariablen (Präfix ``MCP_``).

    Beispiele:
      ``MCP_TRANSPORT=streamable-http`` · ``MCP_HOST=0.0.0.0`` · ``MCP_PORT=8000``

    Default ist der lokale stdio-Betrieb mit Loopback-Binding — Cloud-Betrieb
    wird ausschliesslich explizit über ENV-Vars (oder CLI-Flags) aktiviert.
    """

    model_config = SettingsConfigDict(env_prefix="MCP_", env_file=".env", extra="ignore")

    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000

    # Stateless HTTP: read-only Server hält keinen Session-State → jeder
    # Load-Balancer (Round-Robin) funktioniert ohne Sticky Sessions (SCALE-002/003).
    stateless_http: bool = True
    json_response: bool = False

    # CORS-Origins für Browser-Clients (z. B. claude.ai). Komma-separiert via
    # MCP_CORS_ORIGINS. Default deckt den dokumentierten Browser-Use-Case ab;
    # in Produktion explizit auf die genutzten Origins setzen (keine Wildcard).
    cors_origins: str = "https://claude.ai"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
