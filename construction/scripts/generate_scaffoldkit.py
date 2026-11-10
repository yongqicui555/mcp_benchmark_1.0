from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.content_construct import (
    all_specs as _all_specs,
    clean_mcp_config as _clean_mcp_config,
    generate as _generate,
    l1_l2_spec as _l1_l2_spec,
    l3_spec as _l3_spec,
    render_clean_server as _render_clean_server,
    write_clean_variant as _write_clean_variant,
    write_ground_truth as _write_ground_truth,
)


BASE = "scaffoldkit"


def l1_l2_spec(path_id: str, layer: str) -> dict[str, Any]:
    return _l1_l2_spec(BASE, path_id, layer)


def l3_spec(path_id: str, objective: str) -> dict[str, Any]:
    return _l3_spec(BASE, path_id, objective)


def all_specs(_meta: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return _all_specs(BASE)


def render_clean_server(spec: dict[str, Any]) -> str:
    return _render_clean_server(spec)


def clean_mcp_config(spec: dict[str, Any]) -> dict[str, Any]:
    return _clean_mcp_config(spec)


def write_clean_variant(output_root: Path, seed_dir: Path, spec: dict[str, Any], force: bool) -> None:
    _write_clean_variant(output_root, seed_dir, spec, force)


def write_ground_truth(root: Path, clean_output_root: Path, specs: list[dict[str, Any]]) -> Path:
    return _write_ground_truth(root, clean_output_root, specs, BASE)


def main() -> int:
    return _generate(BASE)


if __name__ == "__main__":
    raise SystemExit(main())
