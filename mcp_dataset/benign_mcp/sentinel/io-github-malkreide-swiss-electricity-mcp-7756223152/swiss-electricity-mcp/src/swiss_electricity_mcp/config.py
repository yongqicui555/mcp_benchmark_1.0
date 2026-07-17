"""Centralised configuration (ARCH-004).

All runtime configuration is read once into a Pydantic-Settings object instead of
scattered ``os.environ`` lookups and module-level globals. Environment variables
use the ``SWISS_ELECTRICITY_`` prefix.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SWISS_ELECTRICITY_",
        extra="ignore",
    )

    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"
    cors_origins: list[str] = []
    env: str = "unknown"  # deployment.environment resource attribute for traces

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, v: object) -> object:
        """Accept a comma-separated string (env var) or an already-parsed list."""
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide Settings singleton."""
    return Settings()
