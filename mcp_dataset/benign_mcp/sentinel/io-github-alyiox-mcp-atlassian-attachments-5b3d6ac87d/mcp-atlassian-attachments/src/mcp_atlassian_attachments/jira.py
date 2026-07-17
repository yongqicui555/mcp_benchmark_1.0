from __future__ import annotations

from typing import Any

from .client import check_response, make_client
from .config import AtlassianConfig, load_config
from .fs import resolve_output_path, sanitize_filename, stream_to_file


def download_jira_attachment(
    attachment_id: str,
    output_dir: str,
    filename: str | None = None,
    overwrite: bool = False,
    *,
    cfg: AtlassianConfig | None = None,
) -> dict[str, Any]:
    cfg = cfg or load_config()

    with make_client(cfg) as client:
        meta_url = f"{cfg.base_url}/rest/api/3/attachment/{attachment_id}"
        meta_resp = client.get(meta_url)
        check_response(meta_resp, "Jira attachment metadata")
        meta = meta_resp.json()

        raw_name = filename if filename else meta["filename"]
        safe_name = sanitize_filename(raw_name)
        output_path = resolve_output_path(output_dir, safe_name)

        content_url: str = meta.get("content") or (f"{cfg.base_url}/rest/api/3/attachment/content/{attachment_id}")
        expected_size: int | None = meta.get("size")

        with client.stream("GET", content_url) as resp:
            check_response(resp, "Jira attachment content")
            bytes_written = stream_to_file(resp, output_path, expected_size, overwrite)

    return {
        "product": "jira",
        "attachmentId": attachment_id,
        "filename": safe_name,
        "mimeType": meta.get("mimeType"),
        "size": bytes_written,
        "path": str(output_path),
        "sourceUrl": content_url,
    }
