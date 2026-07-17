"""Configuration for the Youfiliate MCP server.

All settings come from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Server configuration loaded from environment variables."""

    # DRF backend URL (no trailing slash)
    youfiliate_api_base_url: str = "http://localhost:8000"

    # API key for the MCP server (user provides via client config)
    youfiliate_api_key: str = ""

    # Shared secret for the verify-api-key endpoint
    mcp_server_secret: str = ""

    # Transport: "stdio" for local, "streamable-http" for remote
    transport: str = "stdio"

    # Server port (only used for streamable-http transport)
    port: int = 8080

    # Host binding (127.0.0.1 for local, 0.0.0.0 for Docker)
    host: str = "127.0.0.1"

    # Allowed origins for DNS rebinding protection (comma-separated)
    allowed_origins: str = ""

    # Rate limit: requests per minute per API key
    rate_limit_rpm: int = 60

    # Response character limit
    max_response_chars: int = 25000

    model_config = {
        "env_prefix": "",
        "case_sensitive": False,
    }


settings = Settings()
