from __future__ import annotations

import re
from pathlib import Path

import httpx


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[/\\:*?"<>|]', "_", name)
    name = name.strip(". ")
    return name or "attachment"


def resolve_output_path(output_dir: str, filename: str) -> Path:
    base = Path(output_dir).resolve()
    try:
        base.mkdir(parents=True, exist_ok=True)
    except PermissionError as exc:
        raise PermissionError(f"Cannot create output directory {base}: permission denied") from exc

    target = (base / filename).resolve()
    if target == base or not target.is_relative_to(base):
        raise ValueError(f"Filename '{filename}' would escape the output directory")
    return target


def stream_to_file(
    resp: httpx.Response,
    path: Path,
    expected_size: int | None,
    overwrite: bool,
) -> int:
    if path.exists() and not overwrite:
        raise FileExistsError(f"File already exists: {path}. Set overwrite=true to replace it.")

    bytes_written = 0
    try:
        with path.open("wb") as f:
            for chunk in resp.iter_bytes(chunk_size=65536):
                f.write(chunk)
                bytes_written += len(chunk)
    except PermissionError as exc:
        raise PermissionError(f"Cannot write to {path}: permission denied") from exc

    if expected_size is not None and bytes_written != expected_size:
        path.unlink(missing_ok=True)
        raise ValueError(f"Download size mismatch: expected {expected_size} bytes, got {bytes_written}.")

    return bytes_written
