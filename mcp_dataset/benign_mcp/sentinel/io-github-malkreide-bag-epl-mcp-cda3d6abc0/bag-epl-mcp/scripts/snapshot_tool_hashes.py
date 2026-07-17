#!/usr/bin/env python3
"""
SEC-022: Snapshot der Tool-Definitionen als SHA-256-Hashes.

Erzeugt eine reproduzierbare Manifest-Datei (`tool-hashes.json`) mit einem Hash
pro Tool ueber Name, Beschreibung, Input-Schema und Annotations. Aenderungen an
einer Tool-Definition aendern den Hash und machen so „Rug Pulls" sichtbar; die
CHANGELOG-Disziplin dokumentiert, wann eine Re-Approval durch Nutzer noetig ist.

Verwendung:
    PYTHONPATH=src python scripts/snapshot_tool_hashes.py [ausgabe.json]
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys

from bag_epl_mcp.server import mcp


async def _build_manifest() -> dict:
    tools = await mcp.list_tools()
    entries = {}
    for tool in sorted(tools, key=lambda t: t.name):
        definition = {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema,
            "annotations": tool.annotations.model_dump() if tool.annotations else None,
        }
        canonical = json.dumps(definition, sort_keys=True, ensure_ascii=False)
        entries[tool.name] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {"tool_count": len(entries), "namespace_prefix": "epl_", "hashes": entries}


def main() -> None:
    manifest = asyncio.run(_build_manifest())
    out = json.dumps(manifest, indent=2, ensure_ascii=False)
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w", encoding="utf-8") as fh:
            fh.write(out + "\n")
        print(f"wrote {sys.argv[1]} ({manifest['tool_count']} tools)")
    else:
        print(out)


if __name__ == "__main__":
    main()
