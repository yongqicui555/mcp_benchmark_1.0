from __future__ import annotations

from pathlib import Path

from content_server_runtime import create_mcp, run as _run


def run(spec_path: str | Path | None = None) -> None:
    _run("notevault", spec_path)

