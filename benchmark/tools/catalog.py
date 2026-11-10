"""Read and verify the frozen benchmark without importing or executing samples."""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
BASES = ("devspace", "docforge", "keyvault", "notevault", "scaffoldkit")
EXPECTED = {"benign_connor": 130, "benign_sentinel": 210, **dict.fromkeys(BASES, 137)}


def filesystem_root(root: Path) -> Path:
    root = root.resolve()
    if sys.platform == "win32" and not str(root).startswith("\\\\?\\"):
        return Path("\\\\?\\" + str(root))
    return root


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def within(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError(f"Expected repository-relative path: {relative!r}")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes repository: {relative!r}")
    return path


def read_labels(root: Path = ROOT) -> list[dict]:
    return [row for subset in EXPECTED for row in jsonl(root / "benchmark" / "ground_truth" / subset / "labels.jsonl")]


def statistics(rows: list[dict]) -> dict:
    return {
        "samples": len(rows),
        "subsets": dict(sorted(Counter(row["base"] for row in rows).items())),
        "layers": dict(sorted(Counter(row.get("layer", "imported_benign") for row in rows).items())),
        "malicious": sum(row["malicious_ground_truth"] is True for row in rows),
        "benign_or_gray": sum(row["malicious_ground_truth"] is False for row in rows),
    }


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_inventory(root: Path, records: list[dict]) -> tuple[list[str], int]:
    root = filesystem_root(root)
    errors = []
    seen = set()
    checked = 0
    for record in records:
        rel = record["path"]
        if rel in seen:
            errors.append(f"Duplicate inventory entry: {rel}")
            continue
        seen.add(rel)
        path = within(root, rel)
        if not (rel.startswith("benchmark/mcp_dataset/") or rel.startswith("benchmark/ground_truth/")):
            errors.append(f"Unexpected inventory location: {rel}")
        elif not path.is_file():
            errors.append(f"Missing file: {rel}")
        elif path.stat().st_size != record["bytes"] or digest(path) != record["sha256"]:
            errors.append(f"Checksum mismatch: {rel}")
        else:
            checked += 1
    actual = {
        path.relative_to(root).as_posix()
        for directory in (root / "benchmark/mcp_dataset", root / "benchmark/ground_truth")
        for path in directory.rglob("*") if path.is_file()
    }
    errors.extend(f"Unlisted file: {rel}" for rel in sorted(actual - seen))
    return errors, checked


def verify(root: Path = ROOT) -> dict:
    root = filesystem_root(root)
    errors = []
    rows = read_labels(root)
    ids = set()
    sample_paths = set()
    structural = 0
    for subset, expected in EXPECTED.items():
        subset_rows = jsonl(root / "benchmark/ground_truth" / subset / "labels.jsonl")
        manifest = json.loads((root / "benchmark/ground_truth" / subset / "manifest.json").read_text(encoding="utf-8"))
        if len(subset_rows) != expected or manifest.get("count") != expected:
            errors.append(f"{subset}: expected {expected} labels and manifest count")
        if any(row.get("base") != subset for row in subset_rows):
            errors.append(f"{subset}: row base does not match its label file")
        if subset in BASES:
            layers = Counter(row.get("layer") for row in subset_rows)
            if layers != {"L0": 1, "L1": 17, "L2": 17, "L3": 102}:
                errors.append(f"{subset}: incorrect layer distribution")
        for field in ("label_file", "sample_root", "clean_root", "dataset_root", "benign_root", "malicious_root"):
            if manifest.get(field) and not within(root, manifest[field]).exists():
                errors.append(f"{subset}: missing manifest {field}")
    for row in rows:
        identity = (row["base"], row["mcp_id"])
        if identity in ids:
            errors.append(f"Duplicate sample identity: {identity}")
        ids.add(identity)
        sample = within(root, row["clean_path"])
        if not sample.is_relative_to(root / "benchmark/mcp_dataset"):
            errors.append(f"Sample outside dataset: {identity}")
        if sample in sample_paths:
            errors.append(f"Repeated sample directory: {identity}")
        sample_paths.add(sample)
        if not sample.is_dir():
            errors.append(f"Missing sample: {identity}")
            continue
        if type(row.get("malicious_ground_truth")) is not bool:
            errors.append(f"Non-boolean malicious label: {identity}")
        elif row["malicious_ground_truth"] != (row.get("layer") == "L3"):
            errors.append(f"Inconsistent malicious label: {identity}")
        for field in ("sample_path", "mcp_config", "source_dir"):
            if row.get(field) and not within(root, row[field]).exists():
                errors.append(f"Missing {field}: {identity}")
        for rel in row.get("source_dirs", []):
            if not within(root, rel).is_dir():
                errors.append(f"Missing source_dirs entry: {identity}")
        if row["base"] in BASES:
            try:
                ast.parse((sample / "server.py").read_text(encoding="utf-8"))
                json.loads((sample / "mcp_config.json").read_text(encoding="utf-8"))
                structural += 1
            except (OSError, SyntaxError, ValueError) as exc:
                errors.append(f"Structural check failed for {identity}: {type(exc).__name__}")
    # Check immediate sample directories; nested source directories are not samples.
    parents = [root / "benchmark/mcp_dataset/benign_mcp" / name for name in ("connor", "sentinel")]
    parents += [root / "benchmark/mcp_dataset/benign_mcp/real_l0_l2_stress" / base for base in BASES]
    parents += [root / "benchmark/mcp_dataset/malicious_mcp" / base for base in BASES]
    discovered = {path.resolve() for parent in parents for path in parent.iterdir() if path.is_dir()}
    if discovered != sample_paths:
        errors.append("Sample directories and labels do not correspond one-to-one")
    inventory = jsonl(root / "benchmark/metadata/files.sha256.jsonl")
    inventory_errors, checked = verify_inventory(root, inventory)
    errors.extend(inventory_errors)
    return {
        "ok": not errors,
        **statistics(rows),
        "inventory_files": len(inventory),
        "verified_files": checked,
        "constructed_servers_parsed": structural,
        "sample_code_executed": False,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("stats", "verify", "read"))
    parser.add_argument("--base", choices=tuple(EXPECTED))
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    if args.limit < 0:
        parser.error("--limit must be non-negative")
    try:
        if args.command == "verify":
            result = verify()
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["ok"] else 1
        rows = read_labels()
        if args.base:
            rows = [row for row in rows if row["base"] == args.base]
        if args.command == "stats":
            print(json.dumps(statistics(rows), ensure_ascii=False, indent=2))
        else:
            for row in rows[:args.limit]:
                print(json.dumps(row, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
