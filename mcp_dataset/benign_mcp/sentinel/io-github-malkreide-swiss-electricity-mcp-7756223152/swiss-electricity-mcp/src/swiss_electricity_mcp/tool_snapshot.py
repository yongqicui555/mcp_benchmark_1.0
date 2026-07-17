"""Tool-definition snapshot + hash pinning (SEC-022).

A release-time snapshot of every tool's name, description, annotations and input
schema is hashed and committed to ``tool-definitions.lock.json``. The test suite
re-derives the snapshot from the live server and fails if it drifts from the
committed hash. This turns any tool-surface change (renamed tool, edited
description, changed argument schema) into a deliberate, reviewable act — a
client re-approval signal rather than a silent rug-pull.

Regenerate the lock after an *intended* tool change:

    python -m swiss_electricity_mcp.tool_snapshot --write
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any

# The lock lives at the repository root, next to pyproject.toml.
LOCK_PATH = Path(__file__).resolve().parents[2] / "tool-definitions.lock.json"


async def build_snapshot() -> list[dict[str, Any]]:
    """Derive the canonical tool snapshot from the live server."""
    from .server import mcp

    tools = await mcp.list_tools()
    snapshot: list[dict[str, Any]] = []
    for t in sorted(tools, key=lambda x: x.name):
        annotations = (
            t.annotations.model_dump(exclude_none=True) if t.annotations else {}
        )
        snapshot.append(
            {
                "name": t.name,
                "description": t.description or "",
                "annotations": annotations,
                "input_schema": t.inputSchema,
            }
        )
    return snapshot


def snapshot_hash(snapshot: list[dict[str, Any]]) -> str:
    """Stable SHA-256 over the canonical JSON serialisation of the snapshot."""
    canonical = json.dumps(snapshot, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_lock(snapshot: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "version": 1,
        "tool_count": len(snapshot),
        "sha256": snapshot_hash(snapshot),
        "tools": snapshot,
    }


def write_lock(path: Path = LOCK_PATH) -> dict[str, Any]:
    snapshot = asyncio.run(build_snapshot())
    lock = build_lock(snapshot)
    path.write_text(
        json.dumps(lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return lock


def main() -> None:
    parser = argparse.ArgumentParser(description="Tool-definition snapshot (SEC-022).")
    parser.add_argument(
        "--write", action="store_true", help="(Re)write tool-definitions.lock.json"
    )
    args = parser.parse_args()
    if args.write:
        lock = write_lock()
        print(f"Wrote {LOCK_PATH} ({lock['tool_count']} tools, sha256 {lock['sha256'][:12]})")
    else:
        snapshot = asyncio.run(build_snapshot())
        print(snapshot_hash(snapshot))


if __name__ == "__main__":
    main()
