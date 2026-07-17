#!/usr/bin/env python3
"""Generate the tool-definition hash pin (SEC-022).

Run after any intentional change to a tool's name, description, or schema:

    PYTHONPATH=src python scripts/pin_tools.py

Then commit the updated ``audits/tool-pins/current.json`` together with a
CHANGELOG note (re-approval prompt) describing what changed and why.
"""

from __future__ import annotations

import json
import pathlib
from importlib.metadata import PackageNotFoundError, version

from swiss_cultural_heritage_mcp._toolpins import compute_tool_pins
from swiss_cultural_heritage_mcp.server import mcp

OUT = pathlib.Path(__file__).resolve().parents[1] / "audits" / "tool-pins" / "current.json"


def main() -> None:
    pins = compute_tool_pins(mcp)
    try:
        pkg_version = version("swiss-cultural-heritage-mcp")
    except PackageNotFoundError:
        pkg_version = "0.0.0+local"

    payload = {"generated_for_version": pkg_version, **pins}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(
        f"wrote {OUT.relative_to(OUT.parents[2])} — {pins['tool_count']} tools, "
        f"manifest {pins['manifest_sha256'][:12]}…"
    )


if __name__ == "__main__":
    main()
