from __future__ import annotations

import json

import httpx
import pytest
import respx

from mcp_atlassian_attachments.config import AtlassianConfig, load_config, reset_config

SITE = "https://example.atlassian.net"
CLOUD_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
TENANT_INFO_URL = f"{SITE}/_edge/tenant_info"


@pytest.fixture(autouse=True)
def _reset():
    reset_config()
    yield
    reset_config()


@respx.mock
def test_loads_from_env(monkeypatch):
    monkeypatch.setenv("ATLASSIAN_SITE_URL", SITE)
    monkeypatch.setenv("ATLASSIAN_EMAIL", "user@example.com")
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "tok")
    respx.get(TENANT_INFO_URL).mock(return_value=httpx.Response(200, json={"cloudId": CLOUD_ID}))

    cfg = load_config()

    assert cfg.site_url == SITE
    assert cfg.email == "user@example.com"
    assert cfg.api_token == "tok"
    assert cfg.cloud_id == CLOUD_ID


@respx.mock
def test_strips_trailing_slash(monkeypatch):
    monkeypatch.setenv("ATLASSIAN_SITE_URL", f"{SITE}/")
    monkeypatch.setenv("ATLASSIAN_EMAIL", "u@e.com")
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "t")
    respx.get(TENANT_INFO_URL).mock(return_value=httpx.Response(200, json={"cloudId": CLOUD_ID}))

    cfg = load_config()

    assert cfg.site_url == SITE


@respx.mock
def test_base_url_uses_cloud_id(monkeypatch):
    monkeypatch.setenv("ATLASSIAN_SITE_URL", SITE)
    monkeypatch.setenv("ATLASSIAN_EMAIL", "u@e.com")
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "t")
    respx.get(TENANT_INFO_URL).mock(return_value=httpx.Response(200, json={"cloudId": CLOUD_ID}))

    cfg = load_config()

    assert cfg.base_url == f"https://api.atlassian.com/ex/jira/{CLOUD_ID}"


def test_base_url_property_on_dataclass():
    cfg = AtlassianConfig(
        site_url=SITE,
        email="u@e.com",
        api_token="t",
        cloud_id=CLOUD_ID,
    )
    assert cfg.base_url == f"https://api.atlassian.com/ex/jira/{CLOUD_ID}"


@respx.mock
def test_loads_from_file(monkeypatch, tmp_path):
    monkeypatch.delenv("ATLASSIAN_SITE_URL", raising=False)
    monkeypatch.delenv("ATLASSIAN_EMAIL", raising=False)
    monkeypatch.delenv("ATLASSIAN_API_TOKEN", raising=False)

    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "site_url": "https://file.atlassian.net",
                "email": "file@example.com",
                "api_token": "file-token",
            }
        )
    )

    import mcp_atlassian_attachments.config as cfg_module

    monkeypatch.setattr(cfg_module, "_CONFIG_PATH", config_file)
    respx.get("https://file.atlassian.net/_edge/tenant_info").mock(
        return_value=httpx.Response(200, json={"cloudId": CLOUD_ID})
    )

    cfg = load_config()

    assert cfg.site_url == "https://file.atlassian.net"
    assert cfg.email == "file@example.com"
    assert cfg.api_token == "file-token"
    assert cfg.cloud_id == CLOUD_ID


@respx.mock
def test_env_overrides_file(monkeypatch, tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "site_url": "https://file.atlassian.net",
                "email": "file@example.com",
                "api_token": "file-token",
            }
        )
    )

    import mcp_atlassian_attachments.config as cfg_module

    monkeypatch.setattr(cfg_module, "_CONFIG_PATH", config_file)
    monkeypatch.setenv("ATLASSIAN_SITE_URL", SITE)
    monkeypatch.setenv("ATLASSIAN_EMAIL", "env@example.com")
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "env-token")
    respx.get(TENANT_INFO_URL).mock(return_value=httpx.Response(200, json={"cloudId": CLOUD_ID}))

    cfg = load_config()

    assert cfg.site_url == SITE
    assert cfg.email == "env@example.com"
    assert cfg.api_token == "env-token"


def test_missing_site_url_raises(monkeypatch):
    monkeypatch.delenv("ATLASSIAN_SITE_URL", raising=False)
    monkeypatch.setenv("ATLASSIAN_EMAIL", "u@e.com")
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "t")

    with pytest.raises(ValueError, match="ATLASSIAN_SITE_URL"):
        load_config()


def test_http_site_url_raises(monkeypatch):
    monkeypatch.setenv("ATLASSIAN_SITE_URL", "http://example.atlassian.net")
    monkeypatch.setenv("ATLASSIAN_EMAIL", "u@e.com")
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "t")

    with pytest.raises(ValueError, match="HTTPS"):
        load_config()


def test_missing_email_raises(monkeypatch):
    monkeypatch.setenv("ATLASSIAN_SITE_URL", SITE)
    monkeypatch.delenv("ATLASSIAN_EMAIL", raising=False)
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "t")

    with pytest.raises(ValueError, match="ATLASSIAN_EMAIL"):
        load_config()


def test_missing_api_token_raises(monkeypatch):
    monkeypatch.setenv("ATLASSIAN_SITE_URL", SITE)
    monkeypatch.setenv("ATLASSIAN_EMAIL", "u@e.com")
    monkeypatch.delenv("ATLASSIAN_API_TOKEN", raising=False)

    with pytest.raises(ValueError, match="ATLASSIAN_API_TOKEN"):
        load_config()


def test_error_does_not_leak_token(monkeypatch):
    monkeypatch.setenv("ATLASSIAN_SITE_URL", "http://bad")
    monkeypatch.setenv("ATLASSIAN_EMAIL", "u@e.com")
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "super-secret-token")

    with pytest.raises(ValueError) as exc_info:
        load_config()

    assert "super-secret-token" not in str(exc_info.value)


@respx.mock
def test_tenant_info_http_error_raises(monkeypatch):
    monkeypatch.setenv("ATLASSIAN_SITE_URL", SITE)
    monkeypatch.setenv("ATLASSIAN_EMAIL", "u@e.com")
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "t")
    respx.get(TENANT_INFO_URL).mock(return_value=httpx.Response(404))

    with pytest.raises(RuntimeError, match="Cloud ID"):
        load_config()


@respx.mock
def test_tenant_info_missing_cloud_id_raises(monkeypatch):
    monkeypatch.setenv("ATLASSIAN_SITE_URL", SITE)
    monkeypatch.setenv("ATLASSIAN_EMAIL", "u@e.com")
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "t")
    respx.get(TENANT_INFO_URL).mock(return_value=httpx.Response(200, json={}))

    with pytest.raises(RuntimeError, match="Cloud ID"):
        load_config()
