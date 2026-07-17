from __future__ import annotations

import base64

import httpx

from .config import AtlassianConfig


def _auth_header(cfg: AtlassianConfig) -> str:
    token = base64.b64encode(f"{cfg.email}:{cfg.api_token}".encode()).decode()
    return f"Basic {token}"


def make_client(cfg: AtlassianConfig) -> httpx.Client:
    return httpx.Client(
        headers={"Authorization": _auth_header(cfg)},
        follow_redirects=True,
        timeout=60.0,
    )


def check_response(resp: httpx.Response, context: str) -> None:
    if resp.is_success:
        return
    status = resp.status_code
    if status == 401:
        raise RuntimeError(f"{context}: authentication failed (401). Check ATLASSIAN_EMAIL and ATLASSIAN_API_TOKEN.")
    if status == 403:
        raise RuntimeError(f"{context}: access denied (403). Insufficient permissions.")
    if status == 404:
        raise RuntimeError(f"{context}: not found (404).")
    if status == 416:
        raise RuntimeError(f"{context}: requested range not satisfiable (416).")
    raise RuntimeError(f"{context}: request failed with status {status}.")
