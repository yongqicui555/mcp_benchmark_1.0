from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

import httpx

_CONFIG_PATH = Path.home() / ".config" / "mcp-atlassian-attachments" / "config.json"


def _load_file() -> dict[str, str]:
    if _CONFIG_PATH.exists():
        with _CONFIG_PATH.open() as f:
            return json.load(f)
    return {}


def _resolve_cloud_id(site_url: str) -> str:
    url = f"{site_url}/_edge/tenant_info"
    try:
        resp = httpx.get(url, timeout=10.0)
        resp.raise_for_status()
        cloud_id: str = resp.json()["cloudId"]
        return cloud_id
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Failed to resolve Cloud ID from {url}: {exc}") from exc
    except (KeyError, ValueError) as exc:
        raise RuntimeError(f"Unexpected response from {url} while resolving Cloud ID: {exc}") from exc


@dataclass(frozen=True)
class AtlassianConfig:
    site_url: str
    email: str
    api_token: str
    cloud_id: str = field(default="")

    @property
    def base_url(self) -> str:
        return f"https://api.atlassian.com/ex/jira/{self.cloud_id}"


def load_config() -> AtlassianConfig:
    file_cfg = _load_file()

    site_url = os.environ.get("ATLASSIAN_SITE_URL") or file_cfg.get("site_url", "")
    email = os.environ.get("ATLASSIAN_EMAIL") or file_cfg.get("email", "")
    api_token = os.environ.get("ATLASSIAN_API_TOKEN") or file_cfg.get("api_token", "")

    errors: list[str] = []
    if not site_url:
        errors.append("ATLASSIAN_SITE_URL is required")
    elif not site_url.startswith("https://"):
        errors.append("ATLASSIAN_SITE_URL must be an HTTPS URL")
    if not email:
        errors.append("ATLASSIAN_EMAIL is required")
    if not api_token:
        errors.append("ATLASSIAN_API_TOKEN is required")

    if errors:
        raise ValueError("; ".join(errors))

    site_url = site_url.rstrip("/")
    cloud_id = _resolve_cloud_id(site_url)

    return AtlassianConfig(
        site_url=site_url,
        email=email,
        api_token=api_token,
        cloud_id=cloud_id,
    )


_cached: AtlassianConfig | None = None


def get_config() -> AtlassianConfig:
    global _cached
    if _cached is None:
        _cached = load_config()
    return _cached


def reset_config() -> None:
    global _cached
    _cached = None
