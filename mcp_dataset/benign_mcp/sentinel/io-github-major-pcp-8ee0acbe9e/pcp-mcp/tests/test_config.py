"""Tests for configuration."""

from __future__ import annotations

import pytest

from pcp_mcp.config import PCPMCPSettings


def test_default_settings() -> None:
    settings = PCPMCPSettings()
    assert settings.host == "localhost"
    assert settings.port == 44322
    assert settings.target_host == "localhost"
    assert settings.use_tls is False
    assert settings.tls_verify is True
    assert settings.tls_ca_bundle is None
    assert settings.timeout == 30.0
    assert settings.username is None
    assert settings.password is None


def test_computed_fields_in_model_dump() -> None:
    settings = PCPMCPSettings(host="example.com", port=8080, username="user", password="pass")
    dumped = settings.model_dump()

    assert "base_url" in dumped
    assert dumped["base_url"] == "http://example.com:8080"
    assert "auth" in dumped
    assert dumped["auth"] == ("user", "pass")
    assert "verify" in dumped
    assert dumped["verify"] is True


@pytest.mark.parametrize(
    ("host", "port", "use_tls", "expected_url"),
    [
        ("example.com", 8080, False, "http://example.com:8080"),
        ("example.com", 443, True, "https://example.com:443"),
    ],
)
def test_base_url(
    host: str,
    port: int,
    use_tls: bool,
    expected_url: str,
) -> None:
    settings = PCPMCPSettings(host=host, port=port, use_tls=use_tls)
    assert settings.base_url == expected_url


@pytest.mark.parametrize(
    ("username", "password", "expected_auth"),
    [
        (None, None, None),
        ("user", None, None),
        (None, "pass", None),
        ("user", "pass", ("user", "pass")),
    ],
)
def test_auth_combinations(
    username: str | None,
    password: str | None,
    expected_auth: tuple[str, str] | None,
) -> None:
    settings = PCPMCPSettings(username=username, password=password)
    assert settings.auth == expected_auth


def test_default_allowed_hosts_is_none() -> None:
    settings = PCPMCPSettings()
    assert settings.allowed_hosts is None


@pytest.mark.parametrize(
    ("tls_verify", "tls_ca_bundle", "expected"),
    [
        (True, None, True),
        (False, None, False),
        (True, "/path/to/ca-bundle.crt", "/path/to/ca-bundle.crt"),
        (False, "/path/to/ca-bundle.crt", False),
    ],
    ids=[
        "verify_enabled_default_ca",
        "verify_disabled",
        "verify_with_custom_ca",
        "verify_disabled_ignores_ca_bundle",
    ],
)
def test_verify_property(
    tls_verify: bool,
    tls_ca_bundle: str | None,
    expected: bool | str,
) -> None:
    settings = PCPMCPSettings(tls_verify=tls_verify, tls_ca_bundle=tls_ca_bundle)
    assert settings.verify == expected


@pytest.mark.parametrize(
    ("target_host", "allowed_hosts", "query_host", "expected"),
    [
        ("myhost.example.com", None, "myhost.example.com", True),
        ("localhost", None, "attacker.example.com", False),
        ("localhost", ["web1.example.com"], "web1.example.com", True),
        ("localhost", ["web1.example.com"], "attacker.example.com", False),
        ("localhost", ["*"], "any.host.anywhere.com", True),
        ("localhost", ["*"], "192.168.1.1", True),
        ("localhost", [], "localhost", True),
        ("localhost", [], "other.host.com", False),
    ],
    ids=[
        "target_host_always_allowed",
        "deny_when_allowlist_none",
        "allowlisted_host_permitted",
        "non_allowlisted_host_denied",
        "wildcard_allows_any_host",
        "wildcard_allows_ip",
        "empty_allowlist_permits_target",
        "empty_allowlist_denies_other",
    ],
)
def test_is_host_allowed(
    target_host: str,
    allowed_hosts: list[str] | None,
    query_host: str,
    expected: bool,
) -> None:
    settings = PCPMCPSettings(target_host=target_host, allowed_hosts=allowed_hosts)
    assert settings.is_host_allowed(query_host) is expected
