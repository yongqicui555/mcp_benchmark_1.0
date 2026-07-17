"""Tool-Definitions-Hashing gegen Rug-Pull (SEC-022).

Erzeugt einen reproduzierbaren SHA-256-Snapshot aller Tool-Definitionen
(Name + Beschreibung + Input-Schema). Der Snapshot wird als ``tool-hashes.json``
im Repo versioniert und im Release-Workflow neu berechnet; ein Diff signalisiert
geänderte Tool-Definitionen (Re-Approval-Bedarf, CHANGELOG-Eintrag).

Aufruf:
    python -m parlament_mcp.tool_hashes            # nach stdout
    python -m parlament_mcp.tool_hashes --check     # gegen tool-hashes.json prüfen
    python -m parlament_mcp.tool_hashes --write      # tool-hashes.json schreiben
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from pathlib import Path


async def _collect(mcp) -> dict[str, str]:
    tools = await mcp.list_tools()
    snapshot: dict[str, str] = {}
    for tool in sorted(tools, key=lambda t: t.name):
        canonical = json.dumps(
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema,
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        snapshot[tool.name] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return snapshot


def compute_tool_hashes() -> dict[str, str]:
    """SHA-256-Snapshot aller registrierten Tools berechnen."""
    from parlament_mcp.server import mcp

    return asyncio.run(_collect(mcp))


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    snapshot = compute_tool_hashes()
    path = Path("tool-hashes.json")

    if "--write" in argv:
        path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        sys.stderr.write(f"tool-hashes.json geschrieben ({len(snapshot)} Tools)\n")
        return 0

    if "--check" in argv:
        if not path.exists():
            sys.stderr.write("tool-hashes.json fehlt — erst mit --write erzeugen\n")
            return 1
        stored = json.loads(path.read_text(encoding="utf-8"))
        if stored != snapshot:
            sys.stderr.write("Tool-Definitionen weichen vom gepinnten Snapshot ab!\n")
            sys.stderr.write(json.dumps({"stored": stored, "current": snapshot}, indent=2) + "\n")
            return 1
        sys.stderr.write("Tool-Hashes konsistent.\n")
        return 0

    sys.stdout.write(json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
