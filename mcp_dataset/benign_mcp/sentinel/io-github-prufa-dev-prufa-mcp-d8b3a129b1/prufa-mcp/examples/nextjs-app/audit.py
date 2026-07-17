"""Audit a Next.js app with prufa-mcp."""
from __future__ import annotations

import asyncio
import json
import sys

from prufa_mcp.audit import run_audit


async def main(url: str) -> None:
    result = await run_audit(url=url, wait=True)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python audit.py <url>", file=sys.stderr)
        sys.exit(2)
    asyncio.run(main(sys.argv[1]))
