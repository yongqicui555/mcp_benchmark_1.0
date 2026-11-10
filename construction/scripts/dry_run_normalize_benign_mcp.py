"""Dry-run Sentinel benign MCP normalization.

This script only reads existing Sentinel samples and writes reports under
``benign_mcp/audit``.  It does not modify sample directories, source trees, or
``mcp.json`` files.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SENTINEL_ROOT = PROJECT_ROOT / "benign_mcp" / "sentinel"
DEFAULT_AUDIT_ROOT = PROJECT_ROOT / "benign_mcp" / "audit"

SAFE_DELETE_NAMES = {
    ".DS_Store",
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pycache__",
    "node_modules",
    "venv",
}


def now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def json_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def json_dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def slug(value: str, fallback: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip(".-_")
    return normalized or fallback


def repo_name(repo_url: str, sample_id: str) -> str:
    if not repo_url:
        return sample_id
    parsed = urlparse(repo_url)
    candidate = Path(parsed.path.rstrip("/")).name
    if candidate.endswith(".git"):
        candidate = candidate[:-4]
    return slug(candidate, sample_id)


def rewrite_app_source(value: Any, sample_id: str, project_dir: str) -> Any:
    if isinstance(value, str):
        return value.replace("/app/source", f"/app/{sample_id}/{project_dir}")
    if isinstance(value, list):
        return [rewrite_app_source(item, sample_id, project_dir) for item in value]
    if isinstance(value, dict):
        return {key: rewrite_app_source(item, sample_id, project_dir) for key, item in value.items()}
    return value


def collect_string_changes(before: Any, after: Any, path: str = "$") -> list[dict[str, str]]:
    changes: list[dict[str, str]] = []
    if isinstance(before, str) and isinstance(after, str):
        if before != after:
            changes.append({"json_path": path, "before": before, "after": after})
        return changes
    if isinstance(before, list) and isinstance(after, list):
        for index, (left, right) in enumerate(zip(before, after)):
            changes.extend(collect_string_changes(left, right, f"{path}[{index}]"))
        return changes
    if isinstance(before, dict) and isinstance(after, dict):
        for key in sorted(set(before) & set(after)):
            changes.extend(collect_string_changes(before[key], after[key], f"{path}.{key}"))
        return changes
    return changes


def planned_safe_deletions(sample: Path, project_dir: str) -> list[dict[str, str]]:
    deletions = [
        {
            "path": "provenance.json",
            "reason": "move provenance into ground_truth/audit metadata after normalization",
        }
    ]
    source = sample / "source"
    if not source.is_dir():
        return deletions
    for path in sorted(source.rglob("*")):
        if path.name not in SAFE_DELETE_NAMES:
            continue
        relative = path.relative_to(source).as_posix()
        deletions.append(
            {
                "path": f"{project_dir}/{relative}",
                "current_path": f"source/{relative}",
            "reason": "safe generated/cache/VCS artifact",
            }
        )
    return deletions


def analyze_sample(sample: Path) -> dict[str, Any]:
    sample_id = sample.name
    provenance_path = sample / "provenance.json"
    mcp_path = sample / "mcp.json"
    source = sample / "source"
    provenance = json_load(provenance_path) if provenance_path.is_file() else {}
    project_dir = repo_name(str(provenance.get("repo_url", "")), sample_id)
    if project_dir in {"source", "mcp.json", "provenance.json"}:
        commit = str(provenance.get("commit_sha", ""))[:8]
        project_dir = f"{project_dir}-{commit or sample_id[:8]}"

    current_entries = sorted(item.name for item in sample.iterdir())
    mcp = json_load(mcp_path) if mcp_path.is_file() else None
    rewritten_mcp = rewrite_app_source(mcp, sample_id, project_dir) if mcp is not None else None
    mcp_changes = collect_string_changes(mcp, rewritten_mcp) if mcp is not None else []

    warnings: list[str] = []
    if not source.is_dir():
        warnings.append("missing source/ directory")
    if not mcp_path.is_file():
        warnings.append("missing mcp.json")
    if not provenance_path.is_file():
        warnings.append("missing provenance.json")
    if not mcp_changes:
        warnings.append("mcp.json contains no /app/source path to rewrite")

    return {
        "sample_id": sample_id,
        "repo_url": provenance.get("repo_url"),
        "commit_sha": provenance.get("commit_sha"),
        "current_entries": current_entries,
        "current_layout": {
            "source_dir": "source" if source.is_dir() else None,
            "mcp_json": "mcp.json" if mcp_path.is_file() else None,
            "provenance_json": "provenance.json" if provenance_path.is_file() else None,
        },
        "proposed_layout": {
            "source_dir": project_dir,
            "mcp_json": "mcp.json",
            "metadata_destination": "ground_truth/benign_sentinel/labels.jsonl and/or benign_mcp/audit",
        },
        "planned_moves": [
            {
                "from": "source",
                "to": project_dir,
                "reason": "match Connor-style sample root with one project source directory",
            }
        ],
        "planned_deletions": planned_safe_deletions(sample, project_dir),
        "mcp_json_rewrites": mcp_changes,
        "warnings": warnings,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Sentinel normalization dry-run",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- Samples: `{summary['samples']}`",
        f"- Samples with `source/`: `{summary['samples_with_source']}`",
        f"- Samples with root `provenance.json`: `{summary['samples_with_provenance_json']}`",
        f"- Samples with `/app/source` rewrites: `{summary['samples_with_mcp_rewrites']}`",
        f"- Planned root provenance removals: `{summary['planned_provenance_json_removals']}`",
        f"- Planned cache/VCS deletions inside source trees: `{summary['planned_safe_artifact_deletions']}`",
        f"- Warnings: `{summary['warnings']}`",
        "",
        "## Per-sample plan",
        "",
        "| sample_id | source move | mcp rewrites | planned deletions | warnings |",
        "|---|---:|---:|---:|---|",
    ]
    for sample in report["samples"]:
        move = sample["planned_moves"][0]
        warning_text = "; ".join(sample["warnings"])
        lines.append(
            "| {sample_id} | `{src}` -> `{dst}` | {rewrites} | {deletions} | {warnings} |".format(
                sample_id=sample["sample_id"],
                src=move["from"],
                dst=move["to"],
                rewrites=len(sample["mcp_json_rewrites"]),
                deletions=len(sample["planned_deletions"]),
                warnings=warning_text,
            )
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This is a dry-run report only; no Sentinel sample files were changed.",
            "- `provenance.json` is listed as removable only after equivalent fields are written to ground truth/audit metadata.",
            "- `dist` and `build` are not treated as automatic deletions because some accepted MCP launchers point into generated package output.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_report(sentinel_root: Path) -> dict[str, Any]:
    samples = [analyze_sample(sample) for sample in sorted(sentinel_root.iterdir()) if sample.is_dir()]
    summary = {
        "samples": len(samples),
        "samples_with_source": sum(1 for sample in samples if sample["current_layout"]["source_dir"]),
        "samples_with_provenance_json": sum(1 for sample in samples if sample["current_layout"]["provenance_json"]),
        "samples_with_mcp_rewrites": sum(1 for sample in samples if sample["mcp_json_rewrites"]),
        "planned_provenance_json_removals": sum(
            1 for sample in samples for item in sample["planned_deletions"] if item["path"] == "provenance.json"
        ),
        "planned_safe_artifact_deletions": sum(
            1 for sample in samples for item in sample["planned_deletions"] if item["path"] != "provenance.json"
        ),
        "warnings": sum(len(sample["warnings"]) for sample in samples),
    }
    return {
        "generated_at": now(),
        "sentinel_root": str(sentinel_root),
        "dry_run_only": True,
        "summary": summary,
        "samples": samples,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sentinel-root", type=Path, default=DEFAULT_SENTINEL_ROOT)
    parser.add_argument("--audit-root", type=Path, default=DEFAULT_AUDIT_ROOT)
    parser.add_argument("--json-name", default="normalization-dry-run-sentinel.json")
    parser.add_argument("--md-name", default="normalization-dry-run-sentinel.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.sentinel_root.is_dir():
        raise FileNotFoundError(f"Sentinel root not found: {args.sentinel_root}")
    report = build_report(args.sentinel_root)
    json_path = args.audit_root / args.json_name
    md_path = args.audit_root / args.md_name
    json_dump(json_path, report)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"json": str(json_path), "markdown": str(md_path), "summary": report["summary"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
