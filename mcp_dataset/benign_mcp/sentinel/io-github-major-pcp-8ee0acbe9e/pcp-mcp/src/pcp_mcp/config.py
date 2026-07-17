"""Configuration for the PCP MCP server."""

from __future__ import annotations

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PCPMCPSettings(BaseSettings):
    """Configuration for the PCP MCP server.

    Attributes:
        host: pmproxy host.
        port: pmproxy port.
        use_tls: Use HTTPS for pmproxy connection.
        timeout: Request timeout in seconds.
        target_host: Target pmcd host to monitor (can be remote hostname).
        username: HTTP basic auth user.
        password: HTTP basic auth password.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PCP_",
        extra="ignore",
    )

    host: str = Field(default="localhost", description="pmproxy host")
    port: int = Field(default=44322, description="pmproxy port")
    use_tls: bool = Field(default=False, description="Use HTTPS for pmproxy connection")
    tls_verify: bool = Field(
        default=True,
        description="Verify TLS certificates when use_tls is enabled",
    )
    tls_ca_bundle: str | None = Field(
        default=None,
        description="Path to custom CA bundle for TLS verification",
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    target_host: str = Field(
        default="localhost",
        description="Target pmcd host to monitor (can be remote hostname)",
    )
    username: str | None = Field(default=None, description="HTTP basic auth user")
    password: str | None = Field(default=None, description="HTTP basic auth password")
    allowed_hosts: list[str] | None = Field(
        default=None,
        description=(
            "Allowlist of hostspecs that can be queried via the host parameter. "
            "If None, only the configured target_host is allowed (default). "
            "Set to ['*'] to allow any host (use with caution)."
        ),
    )

    @computed_field
    @property
    def base_url(self) -> str:
        """URL for connecting to pmproxy."""
        scheme = "https" if self.use_tls else "http"
        return f"{scheme}://{self.host}:{self.port}"

    @computed_field
    @property
    def auth(self) -> tuple[str, str] | None:
        """Auth tuple for httpx, or None if no auth configured."""
        if self.username and self.password:
            return (self.username, self.password)
        return None

    @computed_field
    @property
    def verify(self) -> bool | str:
        """TLS verification setting for httpx.

        Returns:
            False if verification disabled, path to CA bundle if specified,
            or True for default system verification.
        """
        if not self.tls_verify:
            return False
        if self.tls_ca_bundle:
            return self.tls_ca_bundle
        return True

    def is_host_allowed(self, host: str) -> bool:
        """Check if a host is allowed by the allowlist.

        Args:
            host: The hostspec to validate.

        Returns:
            True if the host is allowed, False otherwise.
        """
        # Always allow the configured target_host
        if host == self.target_host:
            return True

        # If no allowlist configured, only target_host is allowed
        if self.allowed_hosts is None:
            return False

        # Wildcard allows everything
        if "*" in self.allowed_hosts:
            return True

        # Check exact match in allowlist
        return host in self.allowed_hosts
