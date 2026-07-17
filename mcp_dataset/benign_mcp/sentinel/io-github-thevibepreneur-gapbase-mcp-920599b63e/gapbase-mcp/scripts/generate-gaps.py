#!/usr/bin/env python3
"""
Generate data/gaps.json for gapbase-mcp from the website source of truth.

Reads:
  - ../website/lib/gaps-data.ts (gap metadata)
  - ../website/lib/gap-enrichments.json (enrichment, provides 'solution')

Writes:
  - ../data/gaps.json with 474 gaps, each containing ONLY:
    { id, slug, pain, solution, industry, role, full_blueprint }

Deliberately EXCLUDED from the MCP bundle (paywalled / scraping protection):
  - source_url, author, author_url, date, engagement, full_content,
    workaround, estimated_spend, tech_stack, difficulty, deploy_playbook,
    gtm_playbook, outreach_templates
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

GAPS_TS = "/Users/vatsmax/vibepreneur-projects/website/lib/gaps-data.ts"
ENRICH = "/Users/vatsmax/vibepreneur-projects/website/lib/gap-enrichments.json"
OUT = os.path.join(ROOT, "data", "gaps.json")

BASE_URL = "https://thevibepreneur.com/gaps"
UTM = "utm_source=mcp&utm_medium=tool&utm_campaign=gapbase-mcp"


def main() -> int:
    with open(ENRICH) as f:
        enrichments = json.load(f)

    with open(GAPS_TS) as f:
        ts_content = f.read()

    # Gap objects are JSON on single lines after `export const gapsData`.
    # Find the array opening and iterate lines until the closing ].
    start_marker = "export const gapsData: GapEntry[] = ["
    start = ts_content.find(start_marker)
    if start == -1:
        print("ERROR: could not find gapsData start marker", file=sys.stderr)
        return 1

    body = ts_content[start + len(start_marker):]
    # Each object literal ends with `},` — match non-greedy across braces.
    # The TS file has each gap on its own line, so split by lines and parse.
    gaps_out = []
    missing_enrich = 0

    # Regex to find JSON objects per line — the file format is one per line.
    for line in body.split("\n"):
        stripped = line.strip().rstrip(",")
        if not stripped.startswith("{") or not stripped.endswith("}"):
            continue
        try:
            gap = json.loads(stripped)
        except json.JSONDecodeError:
            continue

        gap_id = gap.get("id")
        if not gap_id:
            continue

        enrich = enrichments.get(gap_id, {})
        solution = enrich.get("solution", "")
        if not solution:
            missing_enrich += 1

        slug = gap.get("slug", "")
        blueprint = f"{BASE_URL}/{slug}?{UTM}" if slug else f"{BASE_URL}?{UTM}"

        gaps_out.append({
            "id": gap_id,
            "slug": slug,
            "pain": gap.get("pain", ""),
            "solution": solution,
            "industry": gap.get("industry", ""),
            "role": gap.get("role", ""),
            "full_blueprint": blueprint,
        })

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(gaps_out, f, indent=2)

    print(f"Wrote {len(gaps_out)} gaps to {OUT}")
    if missing_enrich:
        print(f"WARN: {missing_enrich} gaps missing solution")
    return 0


if __name__ == "__main__":
    sys.exit(main())
