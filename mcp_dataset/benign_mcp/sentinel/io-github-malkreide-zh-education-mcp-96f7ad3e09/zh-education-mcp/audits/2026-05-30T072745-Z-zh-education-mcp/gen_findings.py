#!/usr/bin/env python3
"""Generate finding docs (one per fail/partial) from verification-results.json
+ the check catalog frontmatter. Reproducible helper for Step 5 of the audit.

Usage: python gen_findings.py <audit_dir> <catalog_dir>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

EFFORT = {
    # check_id -> S/M/L/XL remediation effort estimate
    "ARCH-003": "M", "ARCH-004": "M", "ARCH-007": "S", "ARCH-008": "M",
    "ARCH-011": "M", "ARCH-012": "S", "CH-004": "S",
    "OBS-001": "M", "OBS-002": "S", "OBS-003": "M", "OBS-006": "M",
    "OPS-001": "M", "OPS-003": "S",
    "SCALE-001": "S", "SCALE-002": "M", "SCALE-003": "M", "SCALE-004": "S",
    "SCALE-006": "S",
    "SDK-001": "S", "SDK-002": "M", "SDK-003": "M", "SDK-004": "S",
    "SEC-004": "M", "SEC-005": "M", "SEC-007": "M", "SEC-009": "M",
    "SEC-014": "L", "SEC-015": "L", "SEC-018": "S", "SEC-021": "S",
    "SEC-022": "S",
}


def slug(title: str) -> str:
    s = title.lower()
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:50].rstrip("-")


def load_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    fm: dict[str, str] = {}
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return fm
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def main() -> int:
    import json

    audit_dir = Path(sys.argv[1])
    catalog_dir = Path(sys.argv[2])
    vr = json.loads((audit_dir / "verification-results.json").read_text(encoding="utf-8"))
    findings_dir = audit_dir / "findings"
    findings_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    for cid, r in sorted(vr["results"].items()):
        if r["status"] not in ("fail", "partial"):
            continue
        fm = load_frontmatter(catalog_dir / f"{cid}.md")
        title = fm.get("title", cid)
        pdf_ref = fm.get("pdf_ref", "—")
        evidence = "\n".join(f"- {e}" for e in r.get("evidence", [])) or "- (keine)"
        gaps = "\n".join(f"- {g}" for g in r.get("gaps", [])) or "- (keine)"
        effort = EFFORT.get(cid, "M")

        body = f"""## Finding: {cid} — {title}

**Severity:** {r['severity']}
**Status:** open
**Check-Status:** {r['status']}
**Server:** zh-education-mcp
**Check-Reference:** {cid}
**PDF-Reference:** {pdf_ref}

### Observed Behavior / Evidence
{evidence}

### Gaps (Abweichung vom Best-Practice-Katalog)
{gaps}

### Effort Estimate
{effort}  (S < 1d · M 1-3d · L 1-2w · XL >2w)
"""
        out = findings_dir / f"{cid}-{slug(title)}.md"
        out.write_text(body, encoding="utf-8")
        written += 1

    print(f"wrote {written} finding docs to {findings_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
