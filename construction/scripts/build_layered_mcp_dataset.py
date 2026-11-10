"""Build the layered MCP dataset and rewrite real-base ground truth paths.

Managed layout:
  mcp_dataset/benign_mcp/connor
  mcp_dataset/benign_mcp/sentinel
  mcp_dataset/benign_mcp/real_l0_l2_stress/<base>/<L0|L1_*|L2_*>
  mcp_dataset/malicious_mcp/<base>/<L3_*>
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASES = ("devspace", "docforge", "keyvault", "notevault", "scaffoldkit")
DATASET_ROOT = PROJECT_ROOT / "mcp_dataset"
AUDIT_ROOT = PROJECT_ROOT / "benign_mcp" / "audit"
DRY_RUN_JSON = AUDIT_ROOT / "mcp-dataset-layout-dry-run.json"
DRY_RUN_MD = AUDIT_ROOT / "mcp-dataset-layout-dry-run.md"
BUILD_REPORT = AUDIT_ROOT / "mcp-dataset-build-report.json"

IGNORE_NAMES = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".uv-cache",
    ".cache",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
}


def now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def dump_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def ignored(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in IGNORE_NAMES}


def classify_sample(sample_id: str) -> str:
    if sample_id == "L0" or sample_id.startswith("L1_") or sample_id.startswith("L2_"):
        return "benign_stress"
    if sample_id.startswith("L3_"):
        return "malicious"
    raise ValueError(f"Cannot classify sample id: {sample_id}")


def target_for_real_sample(base: str, sample_id: str) -> Path:
    sample_class = classify_sample(sample_id)
    if sample_class == "benign_stress":
        return DATASET_ROOT / "benign_mcp" / "real_l0_l2_stress" / base / sample_id
    return DATASET_ROOT / "malicious_mcp" / base / sample_id


def collect_real_samples() -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for base in BASES:
        source_base = PROJECT_ROOT / "real_mcp" / base
        if not source_base.is_dir():
            raise FileNotFoundError(f"Missing source base: {source_base}")
        for sample in sorted(path for path in source_base.iterdir() if path.is_dir()):
            sample_class = classify_sample(sample.name)
            actions.append(
                {
                    "source": rel(sample),
                    "target": rel(target_for_real_sample(base, sample.name)),
                    "base": base,
                    "sample_id": sample.name,
                    "class": sample_class,
                }
            )
    return actions


def collect_top_level_actions() -> list[dict[str, Any]]:
    top_sources = (
        (PROJECT_ROOT / "benign_mcp" / "connor", DATASET_ROOT / "benign_mcp" / "connor", "benign_connor"),
        (PROJECT_ROOT / "benign_mcp" / "sentinel", DATASET_ROOT / "benign_mcp" / "sentinel", "benign_sentinel"),
    )
    actions = []
    for source, target, sample_class in top_sources:
        if not source.is_dir():
            raise FileNotFoundError(f"Missing source directory: {source}")
        actions.append({"source": rel(source), "target": rel(target), "class": sample_class})
    return actions


def count_by_base(actions: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for action in actions:
        base = action["base"]
        sample_class = action["class"]
        counts.setdefault(base, {"benign_stress": 0, "malicious": 0})
        counts[base][sample_class] += 1
    return counts


def build_plan() -> dict[str, Any]:
    real_actions = collect_real_samples()
    top_level_actions = collect_top_level_actions()
    counts = count_by_base(real_actions)
    errors: list[str] = []
    seen_targets: set[str] = set()
    for action in top_level_actions + real_actions:
        source = PROJECT_ROOT / action["source"]
        target = PROJECT_ROOT / action["target"]
        if not source.exists():
            errors.append(f"missing source: {action['source']}")
        if action["target"] in seen_targets:
            errors.append(f"duplicate target: {action['target']}")
        seen_targets.add(action["target"])
        if target.resolve() == source.resolve():
            errors.append(f"source equals target: {action['source']}")
    return {
        "generated_at": now(),
        "dataset_root": rel(DATASET_ROOT),
        "dry_run_only": True,
        "top_level_actions": top_level_actions,
        "real_sample_actions": real_actions,
        "counts": {
            "connor": len([path for path in (PROJECT_ROOT / "benign_mcp" / "connor").iterdir() if path.is_dir()]),
            "sentinel": len([path for path in (PROJECT_ROOT / "benign_mcp" / "sentinel").iterdir() if path.is_dir()]),
            "real_by_base": counts,
            "real_benign_stress_total": sum(item["benign_stress"] for item in counts.values()),
            "real_malicious_total": sum(item["malicious"] for item in counts.values()),
        },
        "errors": errors,
    }


def write_plan_md(plan: dict[str, Any]) -> None:
    lines = [
        "# MCP dataset layout dry-run",
        "",
        f"- Generated: `{plan['generated_at']}`",
        f"- Dataset root: `{plan['dataset_root']}`",
        f"- Connor samples: `{plan['counts']['connor']}`",
        f"- Sentinel samples: `{plan['counts']['sentinel']}`",
        f"- Real L0-L2 stress samples: `{plan['counts']['real_benign_stress_total']}`",
        f"- Real L3 malicious samples: `{plan['counts']['real_malicious_total']}`",
        f"- Errors: `{len(plan['errors'])}`",
        "",
        "## Real MCP split",
        "",
        "| base | benign stress L0-L2 | malicious L3 |",
        "|---|---:|---:|",
    ]
    for base in BASES:
        item = plan["counts"]["real_by_base"][base]
        lines.append(f"| {base} | {item['benign_stress']} | {item['malicious']} |")
    lines.extend(["", "## Top-level copies", ""])
    for action in plan["top_level_actions"]:
        lines.append(f"- `{action['source']}` -> `{action['target']}`")
    lines.extend(["", "## Errors", ""])
    if plan["errors"]:
        lines.extend(f"- {error}" for error in plan["errors"])
    else:
        lines.append("- None")
    DRY_RUN_MD.parent.mkdir(parents=True, exist_ok=True)
    DRY_RUN_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def remove_managed_targets() -> None:
    targets = [
        DATASET_ROOT / "benign_mcp" / "connor",
        DATASET_ROOT / "benign_mcp" / "sentinel",
        DATASET_ROOT / "benign_mcp" / "real_l0_l2_stress",
        DATASET_ROOT / "malicious_mcp",
    ]
    for target in targets:
        if not target.exists():
            continue
        resolved = target.resolve()
        dataset_resolved = DATASET_ROOT.resolve()
        if dataset_resolved not in resolved.parents:
            raise RuntimeError(f"Refusing to remove path outside dataset root: {target}")
        shutil.rmtree(target)


def copy_actions(actions: list[dict[str, Any]]) -> None:
    for action in actions:
        source = PROJECT_ROOT / action["source"]
        target = PROJECT_ROOT / action["target"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target, ignore=ignored)


def rewrite_ground_truth() -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for base in BASES:
        gt_root = PROJECT_ROOT / "ground_truth" / base
        labels_path = gt_root / "labels.jsonl"
        manifest_path = gt_root / "manifest.json"
        rows: list[dict[str, Any]] = []
        for line in labels_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            sample_id = row["mcp_id"]
            row["clean_path"] = rel(target_for_real_sample(base, sample_id))
            rows.append(row)
        manifest = load_json(manifest_path)
        manifest["clean_root"] = rel(DATASET_ROOT)
        manifest["dataset_root"] = rel(DATASET_ROOT)
        manifest["benign_root"] = rel(DATASET_ROOT / "benign_mcp" / "real_l0_l2_stress" / base)
        manifest["malicious_root"] = rel(DATASET_ROOT / "malicious_mcp" / base)
        manifest["layout"] = "layered_mcp_dataset_v1"
        dump_jsonl(labels_path, rows)
        dump_json(manifest_path, manifest)
        summary[base] = {"labels": len(rows), "manifest_count": manifest.get("count")}
    return summary


def verify() -> dict[str, Any]:
    errors: list[str] = []
    counts: dict[str, Any] = {
        "connor": len([path for path in (DATASET_ROOT / "benign_mcp" / "connor").iterdir() if path.is_dir()]),
        "sentinel": len([path for path in (DATASET_ROOT / "benign_mcp" / "sentinel").iterdir() if path.is_dir()]),
        "real_by_base": {},
    }
    for base in BASES:
        benign_base = DATASET_ROOT / "benign_mcp" / "real_l0_l2_stress" / base
        malicious_base = DATASET_ROOT / "malicious_mcp" / base
        benign_dirs = [path for path in benign_base.iterdir() if path.is_dir()] if benign_base.is_dir() else []
        malicious_dirs = [path for path in malicious_base.iterdir() if path.is_dir()] if malicious_base.is_dir() else []
        counts["real_by_base"][base] = {"benign_stress": len(benign_dirs), "malicious": len(malicious_dirs)}
        for path in benign_dirs:
            if classify_sample(path.name) != "benign_stress":
                errors.append(f"{base}: non L0-L2 in benign stress: {path.name}")
        for path in malicious_dirs:
            if classify_sample(path.name) != "malicious":
                errors.append(f"{base}: non L3 in malicious: {path.name}")
        labels_path = PROJECT_ROOT / "ground_truth" / base / "labels.jsonl"
        manifest_path = PROJECT_ROOT / "ground_truth" / base / "manifest.json"
        rows = [json.loads(line) for line in labels_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        manifest = load_json(manifest_path)
        if len(rows) != 137 or manifest.get("count") != 137:
            errors.append(f"{base}: expected 137 labels/manifest count, got {len(rows)}/{manifest.get('count')}")
        if "clean_mcp" in labels_path.read_text(encoding="utf-8") or "clean_mcp" in manifest_path.read_text(encoding="utf-8"):
            errors.append(f"{base}: ground_truth still contains clean_mcp")
        for row in rows:
            clean_path = PROJECT_ROOT / row["clean_path"]
            if not clean_path.is_dir():
                errors.append(f"{base}: missing clean_path for {row['mcp_id']}: {row['clean_path']}")
            sample_class = classify_sample(row["mcp_id"])
            if sample_class == "benign_stress" and "/benign_mcp/real_l0_l2_stress/" not in row["clean_path"]:
                errors.append(f"{base}: L0-L2 not mapped to benign stress: {row['mcp_id']}")
            if sample_class == "malicious" and "/malicious_mcp/" not in row["clean_path"]:
                errors.append(f"{base}: L3 not mapped to malicious: {row['mcp_id']}")
    return {"ok": not errors, "errors": errors, "counts": counts}


def write_dry_run() -> dict[str, Any]:
    plan = build_plan()
    dump_json(DRY_RUN_JSON, plan)
    write_plan_md(plan)
    return plan


def apply_build() -> dict[str, Any]:
    plan = build_plan()
    if plan["errors"]:
        raise RuntimeError("Dry-run plan has errors; refusing to apply")
    remove_managed_targets()
    copy_actions(plan["top_level_actions"])
    copy_actions(plan["real_sample_actions"])
    ground_truth = rewrite_ground_truth()
    verification = verify()
    report = {
        "generated_at": now(),
        "dataset_root": rel(DATASET_ROOT),
        "ground_truth": ground_truth,
        "plan_counts": plan["counts"],
        "verification": verification,
    }
    dump_json(BUILD_REPORT, report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="copy dataset files and rewrite ground_truth")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.apply:
        print(json.dumps(apply_build(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(write_dry_run(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
