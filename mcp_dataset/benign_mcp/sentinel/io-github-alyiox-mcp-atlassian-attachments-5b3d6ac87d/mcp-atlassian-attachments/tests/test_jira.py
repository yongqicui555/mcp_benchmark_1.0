from __future__ import annotations

import httpx
import pytest
import respx

from mcp_atlassian_attachments.config import AtlassianConfig
from mcp_atlassian_attachments.jira import download_jira_attachment

SITE = "https://test.atlassian.net"
CLOUD_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
CFG = AtlassianConfig(site_url=SITE, email="u@e.com", api_token="tok", cloud_id=CLOUD_ID)

ATTACHMENT_ID = "439535"
BASE = f"https://api.atlassian.com/ex/jira/{CLOUD_ID}"
META_URL = f"{BASE}/rest/api/3/attachment/{ATTACHMENT_ID}"
CONTENT_URL = f"{BASE}/rest/api/3/attachment/content/{ATTACHMENT_ID}"
FILE_CONTENT = b"fake png data"


def _meta(filename="test.png", mime="image/png", size=None, content_url=None):
    meta = {
        "id": ATTACHMENT_ID,
        "filename": filename,
        "mimeType": mime,
        "content": content_url or CONTENT_URL,
    }
    if size is not None:
        meta["size"] = size
    return meta


@respx.mock
def test_downloads_jira_attachment(tmp_path):
    respx.get(META_URL).mock(return_value=httpx.Response(200, json=_meta()))
    respx.get(CONTENT_URL).mock(return_value=httpx.Response(200, content=FILE_CONTENT))

    result = download_jira_attachment(ATTACHMENT_ID, str(tmp_path), cfg=CFG)

    assert result["product"] == "jira"
    assert result["attachmentId"] == ATTACHMENT_ID
    assert result["filename"] == "test.png"
    assert result["mimeType"] == "image/png"
    assert result["size"] == len(FILE_CONTENT)
    saved = tmp_path / "test.png"
    assert saved.exists()
    assert saved.read_bytes() == FILE_CONTENT


@respx.mock
def test_uses_filename_override(tmp_path):
    respx.get(META_URL).mock(return_value=httpx.Response(200, json=_meta()))
    respx.get(CONTENT_URL).mock(return_value=httpx.Response(200, content=FILE_CONTENT))

    result = download_jira_attachment(ATTACHMENT_ID, str(tmp_path), filename="custom.png", cfg=CFG)

    assert result["filename"] == "custom.png"
    assert (tmp_path / "custom.png").exists()


@respx.mock
def test_verifies_size_match(tmp_path):
    respx.get(META_URL).mock(return_value=httpx.Response(200, json=_meta(size=len(FILE_CONTENT))))
    respx.get(CONTENT_URL).mock(return_value=httpx.Response(200, content=FILE_CONTENT))

    result = download_jira_attachment(ATTACHMENT_ID, str(tmp_path), cfg=CFG)

    assert result["size"] == len(FILE_CONTENT)


@respx.mock
def test_size_mismatch_raises(tmp_path):
    respx.get(META_URL).mock(return_value=httpx.Response(200, json=_meta(size=9999)))
    respx.get(CONTENT_URL).mock(return_value=httpx.Response(200, content=FILE_CONTENT))

    with pytest.raises(ValueError, match="mismatch"):
        download_jira_attachment(ATTACHMENT_ID, str(tmp_path), cfg=CFG)


@respx.mock
def test_raises_on_401(tmp_path):
    respx.get(META_URL).mock(return_value=httpx.Response(401))

    with pytest.raises(RuntimeError, match="401"):
        download_jira_attachment(ATTACHMENT_ID, str(tmp_path), cfg=CFG)

    assert "tok" not in str(pytest.raises(RuntimeError))


@respx.mock
def test_raises_on_403(tmp_path):
    respx.get(META_URL).mock(return_value=httpx.Response(403))

    with pytest.raises(RuntimeError, match="403"):
        download_jira_attachment(ATTACHMENT_ID, str(tmp_path), cfg=CFG)


@respx.mock
def test_raises_on_404(tmp_path):
    respx.get(META_URL).mock(return_value=httpx.Response(404))

    with pytest.raises(RuntimeError, match="404"):
        download_jira_attachment(ATTACHMENT_ID, str(tmp_path), cfg=CFG)


@respx.mock
def test_raises_on_existing_file(tmp_path):
    (tmp_path / "test.png").write_bytes(b"existing")
    respx.get(META_URL).mock(return_value=httpx.Response(200, json=_meta()))
    respx.get(CONTENT_URL).mock(return_value=httpx.Response(200, content=FILE_CONTENT))

    with pytest.raises(FileExistsError):
        download_jira_attachment(ATTACHMENT_ID, str(tmp_path), cfg=CFG)


@respx.mock
def test_overwrites_existing_file(tmp_path):
    (tmp_path / "test.png").write_bytes(b"old")
    respx.get(META_URL).mock(return_value=httpx.Response(200, json=_meta()))
    respx.get(CONTENT_URL).mock(return_value=httpx.Response(200, content=FILE_CONTENT))

    result = download_jira_attachment(ATTACHMENT_ID, str(tmp_path), overwrite=True, cfg=CFG)

    assert (tmp_path / "test.png").read_bytes() == FILE_CONTENT
    assert result["size"] == len(FILE_CONTENT)


@respx.mock
def test_creates_output_dir(tmp_path):
    new_dir = tmp_path / "nested" / "dir"
    respx.get(META_URL).mock(return_value=httpx.Response(200, json=_meta()))
    respx.get(CONTENT_URL).mock(return_value=httpx.Response(200, content=FILE_CONTENT))

    download_jira_attachment(ATTACHMENT_ID, str(new_dir), cfg=CFG)

    assert new_dir.is_dir()
    assert (new_dir / "test.png").exists()


@respx.mock
def test_error_does_not_leak_token(tmp_path):
    respx.get(META_URL).mock(return_value=httpx.Response(401))

    with pytest.raises(RuntimeError) as exc_info:
        download_jira_attachment(ATTACHMENT_ID, str(tmp_path), cfg=CFG)

    assert "tok" not in str(exc_info.value)
    assert CFG.email not in str(exc_info.value)
