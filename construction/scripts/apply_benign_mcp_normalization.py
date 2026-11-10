"""Apply benign MCP normalization and write benign ground truth labels."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BENIGN_ROOT = PROJECT_ROOT / "benign_mcp"
DRY_RUN_PATH = BENIGN_ROOT / "audit" / "normalization-dry-run-sentinel.json"
GROUND_TRUTH_ROOT = PROJECT_ROOT / "ground_truth"


def now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def json_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def json_dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def jsonl_dump(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(relative + b"\0" + sha256_file(path).encode("ascii") + b"\n")
    return digest.hexdigest()


def rewrite_app_source(value: Any, sample_id: str, project_dir: str) -> Any:
    if isinstance(value, str):
        return value.replace("/app/source", f"/app/{sample_id}/{project_dir}")
    if isinstance(value, list):
        return [rewrite_app_source(item, sample_id, project_dir) for item in value]
    if isinstance(value, dict):
        return {key: rewrite_app_source(item, sample_id, project_dir) for key, item in value.items()}
    return value


def relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()


def validate_sample_plan(sample_root: Path, plan: dict[str, Any]) -> None:
    if not sample_root.is_dir():
        raise FileNotFoundError(f"Missing Sentinel sample: {sample_root}")
    if not (sample_root / "source").is_dir():
        raise FileNotFoundError(f"Missing source/ before normalization: {sample_root}")
    if not (sample_root / "mcp.json").is_file():
        raise FileNotFoundError(f"Missing mcp.json: {sample_root}")
    if not (sample_root / "provenance.json").is_file():
        raise FileNotFoundError(f"Missing provenance.json: {sample_root}")
    target = sample_root / plan["proposed_layout"]["source_dir"]
    if target.exists():
        raise FileExistsError(f"Target source directory already exists: {target}")


def launcher_from_mcp(mcp: dict[str, Any], sample_id: str) -> dict[str, Any] | None:
    servers = mcp.get("mcpServers")
    if not isinstance(servers, dict) or not servers:
        return None
    server = servers.get(sample_id)
    if server is None and len(servers) == 1:
        server = next(iter(servers.values()))
    if not isinstance(server, dict):
        return None
    return {
        "command": server.get("command"),
        "args": server.get("args", []),
    }


def sentinel_label(sample_root: Path, plan: dict[str, Any], provenance: dict[str, Any], mcp: dict[str, Any]) -> dict[str, Any]:
    sample_id = sample_root.name
    project_dir = plan["proposed_layout"]["source_dir"]
    source_dir = sample_root / project_dir
    return {
        "base": "benign_sentinel",
        "source": "sentinel",
        "mcp_id": sample_id,
        "sample_path": relative(sample_root),
        "clean_path": relative(sample_root),
        "mcp_config": relative(sample_root / "mcp.json"),
        "source_dir": relative(source_dir),
        "source_dirs": [relative(source_dir)],
        "label": "benign",
        "risk_layer": "benign",
        "malicious_ground_truth": False,
        "admission_policy": provenance.get("admission_policy", "source_scan_only_no_confirmed_malicious_behavior"),
        "registry_name": provenance.get("registry_name"),
        "registry_version": provenance.get("registry_version"),
        "repo_url": provenance.get("repo_url"),
        "commit_sha": provenance.get("commit_sha"),
        "license": provenance.get("license"),
        "entrypoint": provenance.get("entrypoint"),
        "launcher": launcher_from_mcp(mcp, sample_id),
        "original_source_sha256": provenance.get("source_sha256"),
        "normalized_source_sha256": tree_hash(source_dir),
        "source_file_count": provenance.get("source_file_count"),
        "source_text_bytes": provenance.get("source_text_bytes"),
        "review_evidence": "benign_mcp/audit/reviews-imported.json",
        "expected_trigger": None,
        "evidence_endpoint": None,
        "evidence_key": None,
        "notes": [],
    }


def connor_label(sample_root: Path) -> dict[str, Any]:
    source_dirs = [path for path in sorted(sample_root.iterdir()) if path.is_dir()]
    return {
        "base": "benign_connor",
        "source": "connor",
        "mcp_id": sample_root.name,
        "sample_path": relative(sample_root),
        "clean_path": relative(sample_root),
        "mcp_config": relative(sample_root / "mcp.json"),
        "source_dir": relative(source_dirs[0]) if len(source_dirs) == 1 else None,
        "source_dirs": [relative(path) for path in source_dirs],
        "label": "benign",
        "risk_layer": "benign",
        "malicious_ground_truth": False,
        "admission_policy": "connor_original_benign_copy",
        "source_sha256": tree_hash(sample_root),
        "expected_trigger": None,
        "evidence_endpoint": None,
        "evidence_key": None,
        "notes": [] if len(source_dirs) == 1 else [f"sample has {len(source_dirs)} source directories"],
    }


def write_ground_truth(base: str, rows: list[dict[str, Any]], sample_root: Path) -> None:
    gt_root = GROUND_TRUTH_ROOT / base
    labels_path = gt_root / "labels.jsonl"
    manifest = {
        "base": base,
        "schema_version": 1,
        "count": len(rows),
        "label_file": relative(labels_path),
        "sample_root": relative(sample_root),
        "malicious_count": 0,
        "benign_count": len(rows),
        "source": rows[0]["source"] if rows else base,
        "admission_policy": rows[0]["admission_policy"] if rows else None,
    }
    jsonl_dump(labels_path, rows)
    json_dump(gt_root / "manifest.json", manifest)


def normalize_sentinel(report: dict[str, Any]) -> list[dict[str, Any]]:
    labels: list[dict[str, Any]] = []
    sentinel_root = BENIGN_ROOT / "sentinel"
    for plan in report["samples"]:
        sample_id = plan["sample_id"]
        sample_root = sentinel_root / sample_id
        validate_sample_plan(sample_root, plan)
        project_dir = plan["proposed_layout"]["source_dir"]
        provenance = json_load(sample_root / "provenance.json")
        mcp = json_load(sample_root / "mcp.json")
        rewritten_mcp = rewrite_app_source(mcp, sample_id, project_dir)

        (sample_root / "source").rename(sample_root / project_dir)
        for deletion in plan["planned_deletions"]:
            if deletion["path"] == "provenance.json":
                continue
            target = sample_root / deletion["path"]
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
        json_dump(sample_root / "mcp.json", rewritten_mcp)
        labels.append(sentinel_label(sample_root, plan, provenance, rewritten_mcp))
        (sample_root / "provenance.json").unlink()
    return labels


def write_connor_ground_truth() -> list[dict[str, Any]]:
    connor_root = BENIGN_ROOT / "connor"
    labels = [connor_label(path) for path in sorted(connor_root.iterdir()) if path.is_dir()]
    write_ground_truth("benign_connor", labels, connor_root)
    return labels


def verify_normalized() -> dict[str, Any]:
    errors: list[str] = []
    sentinel_root = BENIGN_ROOT / "sentinel"
    connor_root = BENIGN_ROOT / "connor"
    sentinel_samples = [path for path in sorted(sentinel_root.iterdir()) if path.is_dir()]
    connor_samples = [path for path in sorted(connor_root.iterdir()) if path.is_dir()]
    for sample in sentinel_samples:
        if (sample / "source").exists():
            errors.append(f"Sentinel sample still has source/: {sample.name}")
        if (sample / "provenance.json").exists():
            errors.append(f"Sentinel sample still has provenance.json: {sample.name}")
        if "/app/source" in (sample / "mcp.json").read_text(encoding="utf-8"):
            errors.append(f"Sentinel mcp.json still references /app/source: {sample.name}")
        dirs = [path for path in sample.iterdir() if path.is_dir()]
        if len(dirs) != 1:
            errors.append(f"Sentinel sample should have exactly one source dir: {sample.name}")
    for base, expected, root in (
        ("benign_sentinel", len(sentinel_samples), sentinel_root),
        ("benign_connor", len(connor_samples), connor_root),
    ):
        labels_path = GROUND_TRUTH_ROOT / base / "labels.jsonl"
        manifest_path = GROUND_TRUTH_ROOT / base / "manifest.json"
        if not labels_path.is_file() or not manifest_path.is_file():
            errors.append(f"Missing ground truth files for {base}")
            continue
        labels = [json.loads(line) for line in labels_path.read_text(encoding="utf-8").splitlines() if line]
        if len(labels) != expected:
            errors.append(f"{base} labels count {len(labels)} != {expected}")
        for label in labels:
            if label.get("malicious_ground_truth") is not False:
                errors.append(f"{base} non-benign label: {label.get('mcp_id')}")
            if not (PROJECT_ROOT / label["sample_path"]).is_dir():
                errors.append(f"{base} missing sample_path: {label.get('mcp_id')}")
            if not (PROJECT_ROOT / label["mcp_config"]).is_file():
                errors.append(f"{base} missing mcp_config: {label.get('mcp_id')}")
        manifest = json_load(manifest_path)
        if manifest.get("count") != expected or manifest.get("sample_root") != relative(root):
            errors.append(f"{base} manifest mismatch")
    return {
        "ok": not errors,
        "errors": errors,
        "connor": len(connor_samples),
        "sentinel": len(sentinel_samples),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run-report", type=Path, default=DRY_RUN_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = json_load(args.dry_run_report)
    if not report.get("dry_run_only"):
        raise ValueError(f"Unexpected dry-run report format: {args.dry_run_report}")
    sentinel_labels = normalize_sentinel(report)
    write_ground_truth("benign_sentinel", sentinel_labels, BENIGN_ROOT / "sentinel")
    connor_labels = write_connor_ground_truth()
    verification = verify_normalized()
    result = {
        "generated_at": now(),
        "sentinel_normalized": len(sentinel_labels),
        "connor_labels": len(connor_labels),
        "verification": verification,
    }
    json_dump(BENIGN_ROOT / "audit" / "normalization-apply-report.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if verification["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
