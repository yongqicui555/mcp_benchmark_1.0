"""Build the provenance-backed benign MCP dataset.

The command deliberately separates candidate acquisition, static evidence,
independent source reviews, optional runtime validation, and final admission.
For the current dataset policy, a Sentinel sample is admitted by source scan:
hard static gates plus two independent code-review rounds that find no
malicious behavior.  No candidate source is executed unless the explicit
``runtime`` command is run.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONNOR_ROOT = PROJECT_ROOT / "inputs" / "connor" / "Benign" / "benign_servers"
DEFAULT_SENTINEL_ROOT = PROJECT_ROOT / "inputs" / "sentinel"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "benign_mcp"
ENRICHMENT_FILE = "enriched-registry-2026-06-18T08-48-59-206Z.csv"
REGISTRY_FILE = "mcp-registry-crawl-2026-06-18T06-18-18-391Z.json"

MAX_FIRST_PARTY_FILES = 100
MAX_FIRST_PARTY_TEXT_BYTES = 5 * 1024 * 1024
MIN_CANDIDATE_POOL = 600
FINAL_SENTINEL_COUNT = 300
ALLOWED_LANGUAGES = {"Python", "TypeScript", "JavaScript"}
ALLOWED_PACKAGE_TYPES = {"npm", "pypi"}
EXCLUDED_PARTS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "coverage",
}
BINARY_SUFFIXES = {
    ".7z", ".a", ".bin", ".bmp", ".class", ".dll", ".dylib", ".exe",
    ".gif", ".gz", ".ico", ".jar", ".jpeg", ".jpg", ".lock", ".mp3",
    ".mp4", ".otf", ".pdf", ".png", ".so", ".tar", ".ttf", ".wav", ".webp",
    ".woff", ".woff2", ".zip",
}
SOURCE_SUFFIXES = {
    ".c", ".cc", ".cs", ".go", ".java", ".js", ".jsx", ".mjs", ".mts",
    ".php", ".py", ".rb", ".rs", ".sh", ".ts", ".tsx", ".vue", ".yaml",
    ".yml", ".json", ".toml", ".ini", ".cfg", ".md",
}
LICENSE_FILES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "COPYING.md")


@dataclass(frozen=True)
class Candidate:
    sample_id: str
    registry_name: str
    registry_version: str
    repo_url: str
    primary_language: str
    package: dict[str, Any]
    requires_api_key: bool
    required_env_vars: str
    enrichment_status: str


def now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def stable_sample_id(registry_name: str, repo_url: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", registry_name.lower()).strip("-")[:72]
    digest = hashlib.sha256(repo_url.lower().encode("utf-8")).hexdigest()[:10]
    return f"{slug}-{digest}"


def json_dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def json_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def run(command: list[str], *, cwd: Path | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def remove_tree(path: Path) -> None:
    """Remove only pipeline-owned partial clones, including Git read-only pack files."""
    if not path.exists():
        return

    def retry(function: Any, value: str, exc: Any) -> None:
        if isinstance(exc[1], FileNotFoundError):
            return
        try:
            os.chmod(value, stat.S_IWRITE)
        except FileNotFoundError:
            return
        function(value)

    last_error: PermissionError | None = None
    for _attempt in range(5):
        try:
            shutil.rmtree(path, onerror=retry)
            return
        except FileNotFoundError:
            return
        except PermissionError as exc:
            last_error = exc
            time.sleep(1)
    assert last_error is not None
    raise last_error


def safe_relpath(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def has_excluded_part(path: Path) -> bool:
    return any(part.lower() in EXCLUDED_PARTS for part in path.parts)


def is_text_source(path: Path) -> bool:
    return path.suffix.lower() in SOURCE_SUFFIXES or path.name in {
        "Dockerfile", "Makefile", "Procfile", "package.json", "pyproject.toml",
        "requirements.txt", "Pipfile", "setup.py", "setup.cfg",
    }


def read_text(path: Path) -> str | None:
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\0" in raw[:8192]:
        return None
    return raw.decode("utf-8", errors="replace")


def copy_connor(connor_root: Path, output_root: Path) -> dict[str, Any]:
    if not connor_root.is_dir():
        raise FileNotFoundError(f"Connor source not found: {connor_root}")
    target = output_root / "connor"
    target.mkdir(parents=True, exist_ok=True)
    source_names = {path.name for path in connor_root.iterdir() if path.is_dir()}
    target_names = {path.name for path in target.iterdir() if path.is_dir()}
    unexpected = target_names - source_names
    if unexpected:
        raise RuntimeError(f"Connor target contains unexpected directories: {sorted(unexpected)}")
    records: list[dict[str, Any]] = []
    for source in sorted(p for p in connor_root.iterdir() if p.is_dir()):
        destination = target / source.name
        if destination.exists():
            if tree_hash(source) != tree_hash(destination):
                raise RuntimeError(f"Existing Connor copy differs from source: {source.name}")
        else:
            shutil.copytree(source, destination, copy_function=shutil.copy2)
        records.append(
            {
                "sample_id": source.name,
                "source_path": str(source),
                "destination_path": safe_relpath(destination, output_root),
                "source_tree_sha256": tree_hash(source),
                "destination_tree_sha256": tree_hash(destination),
                "mcp_json_valid": validate_json(destination / "mcp.json"),
            }
        )
    if len(records) != 130:
        raise RuntimeError(f"Expected 130 Connor samples, copied {len(records)}")
    if any(x["source_tree_sha256"] != x["destination_tree_sha256"] for x in records):
        raise RuntimeError("Connor copy hash mismatch")
    audit = output_root / "audit"
    json_dump(audit / "connor-copy-manifest.json", {"generated_at": now(), "samples": records})
    return {"count": len(records), "manifest": str(audit / "connor-copy-manifest.json")}


def validate_json(path: Path) -> bool:
    try:
        json_load(path)
    except (OSError, ValueError):
        return False
    return True


def load_registry_candidates(sentinel_root: Path) -> list[Candidate]:
    enrichment_path = sentinel_root / "enrichment" / ENRICHMENT_FILE
    registry_path = sentinel_root / "crawls" / REGISTRY_FILE
    with enrichment_path.open(encoding="utf-8-sig", newline="") as handle:
        enrichment_rows = list(csv.DictReader(handle))
    registry_rows = json_load(registry_path)
    registry_index = {
        (row["name"], row["version"], row.get("repo_url", "").rstrip("/").lower()): row
        for row in registry_rows
    }
    best_by_repo: dict[str, tuple[tuple[int, int, int, str], Candidate]] = {}
    for row in enrichment_rows:
        repo_url = row.get("repo_url", "").rstrip("/")
        if not repo_url.startswith("https://github.com/"):
            continue
        language = row.get("primary_language", "")
        if language not in ALLOWED_LANGUAGES:
            continue
        if row.get("enrichment_status") not in {"success", "partial"}:
            continue
        registry = registry_index.get((row["name"], row["version"], repo_url.lower()))
        if not registry or not registry.get("is_latest") or registry.get("status") != "active":
            continue
        packages = [
            package
            for package in registry.get("packages", [])
            if package.get("registryType") in ALLOWED_PACKAGE_TYPES
            and package.get("identifier")
            and package.get("transport", {}).get("type") == "stdio"
        ]
        if not packages:
            continue
        package = sorted(packages, key=lambda x: (x.get("registryType"), x.get("identifier")))[0]
        candidate = Candidate(
            sample_id=stable_sample_id(row["name"], repo_url),
            registry_name=row["name"],
            registry_version=row["version"],
            repo_url=repo_url,
            primary_language=language,
            package=package,
            requires_api_key=row.get("requires_api_key", "").lower() == "true",
            required_env_vars=row.get("required_env_vars", ""),
            enrichment_status=row.get("enrichment_status", ""),
        )
        priority = (
            int(not candidate.requires_api_key and not candidate.required_env_vars),
            int(row.get("dockerfile_present", "").lower() == "false"),
            int(row.get("install_script_count", "0") in {"", "0"}),
            candidate.registry_name,
        )
        key = repo_url.lower()
        if key not in best_by_repo or priority > best_by_repo[key][0]:
            best_by_repo[key] = (priority, candidate)
    # The enrichment snapshot covers only 3,000 of the 13,170 local registry
    # records.  Add the remaining local registry records after all enriched
    # candidates; they receive the identical clone, static-audit, two-review,
    # and isolated-runtime gates and are never admitted on registry metadata.
    for registry in registry_rows:
        repo_url = registry.get("repo_url", "").rstrip("/")
        if not repo_url.startswith("https://github.com/") or not registry.get("is_latest"):
            continue
        if registry.get("status") != "active" or repo_url.lower() in best_by_repo:
            continue
        packages = [
            package
            for package in registry.get("packages", [])
            if package.get("registryType") in ALLOWED_PACKAGE_TYPES
            and package.get("identifier")
            and package.get("transport", {}).get("type") == "stdio"
        ]
        if not packages:
            continue
        package = sorted(packages, key=lambda x: (x.get("registryType"), x.get("identifier")))[0]
        env = registry.get("environment_variables", [])
        env_names = "|".join(sorted(str(item) for item in env))
        candidate = Candidate(
            sample_id=stable_sample_id(registry["name"], repo_url),
            registry_name=registry["name"],
            registry_version=registry["version"],
            repo_url=repo_url,
            primary_language="Python" if package["registryType"] == "pypi" else "JavaScript",
            package=package,
            requires_api_key=any(re.search(r"(?:api[_-]?key|token|secret)", str(item), re.I) for item in env),
            required_env_vars=env_names,
            enrichment_status="registry_only",
        )
        best_by_repo[repo_url.lower()] = ((-1, -1, -1, candidate.registry_name), candidate)
    return [value[1] for value in sorted(best_by_repo.values(), key=lambda x: x[0], reverse=True)]


def git_clone(candidate: Candidate, staging_root: Path) -> tuple[Path | None, dict[str, Any]]:
    target = staging_root / candidate.sample_id / "source"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return None, {"status": "rejected", "reason": "staging_target_already_exists"}
    command = [
        "git", "-c", "http.proxy=", "-c", "https.proxy=", "clone", "--depth", "1",
        "--no-tags", candidate.repo_url, str(target),
    ]
    try:
        result = run(command, timeout=180)
    except subprocess.TimeoutExpired:
        return None, {"status": "rejected", "reason": "git_clone_timeout"}
    if result.returncode:
        remove_tree(target)
        return None, {
            "status": "rejected",
            "reason": "git_clone_failed",
            "git_stderr": result.stderr[-4000:],
        }
    revision = run(["git", "rev-parse", "HEAD"], cwd=target)
    if revision.returncode:
        remove_tree(target)
        return None, {"status": "rejected", "reason": "git_revision_unavailable"}
    commit_sha = revision.stdout.strip()
    remove_tree(target / ".git")
    return target, {"status": "cloned", "commit_sha": commit_sha}


STATIC_RULES: dict[str, tuple[str, re.Pattern[str]]] = {
    "credential_path": (
        "Access to credential, key, browser-profile, or cloud-credential paths.",
        re.compile(r"(?:\.ssh|id_rsa|id_ed25519|\.aws|credentials|\.env|keychain|cookies|login data)", re.I),
    ),
    "process_execution": (
        "Process or shell execution primitive.",
        re.compile(r"(?:subprocess\.|os\.system|child_process|exec(?:File|Sync)?\(|spawn(?:Sync)?\(|shell=True|powershell|cmd\.exe|/bin/sh|bash\s+-c)", re.I),
    ),
    "dynamic_execution": (
        "Dynamic code execution or unsafe deserialization primitive.",
        re.compile(r"(?:\beval\(|\bexec\(|new Function\(|pickle\.loads|yaml\.load\(|marshal\.loads|base64\.b64decode)", re.I),
    ),
    "download_execute": (
        "Potential download-and-execute chain.",
        re.compile(r"(?:curl|wget|invoke-webrequest).{0,160}(?:\||;|&&).{0,80}(?:sh|bash|python|node|powershell)", re.I),
    ),
    "persistence": (
        "Persistence or scheduled-task primitive.",
        re.compile(r"(?:authorized_keys|crontab|launchd|systemctl|schtasks|startup folder|registry\\\\run)", re.I),
    ),
    "obfuscation": (
        "Obfuscation or encoded payload indicator.",
        re.compile(r"(?:fromCharCode|atob\(|btoa\(|base64\s+-d|rot13|\\\\x[0-9a-f]{2})", re.I),
    ),
}


def discover_license(source: Path) -> str | None:
    for name in LICENSE_FILES:
        candidate = source / name
        if candidate.is_file():
            return name
    return None


def source_files(source: Path) -> list[Path]:
    return [
        path
        for path in source.rglob("*")
        if path.is_file() and not has_excluded_part(path.relative_to(source))
    ]


def determine_launcher(source: Path, language: str) -> dict[str, Any] | None:
    """Return only direct executable file launchers; never synthesize shell wrappers."""
    if language in {"TypeScript", "JavaScript"}:
        package_json = source / "package.json"
        if not package_json.is_file():
            return None
        try:
            package = json_load(package_json)
        except ValueError:
            return None
        bin_value = package.get("bin")
        candidates: list[str] = []
        if isinstance(bin_value, str):
            candidates.append(bin_value)
        elif isinstance(bin_value, dict):
            candidates.extend(str(value) for value in bin_value.values())
        main = package.get("main")
        if isinstance(main, str):
            candidates.append(main)
        for value in candidates:
            path = (source / value).resolve()
            if path.is_file() and path.suffix.lower() in {".js", ".mjs", ".cjs"}:
                relative = safe_relpath(path, source)
                return {"command": "node", "args": [f"/app/source/{relative}"], "entrypoint": relative}
        return None
    if language == "Python":
        priority = ("server.py", "main.py", "mcp_server.py", "app.py")
        all_files = source_files(source)
        for name in priority:
            matches = sorted(path for path in all_files if path.name == name)
            if matches:
                relative = safe_relpath(matches[0], source)
                return {"command": "python", "args": [f"/app/source/{relative}"], "entrypoint": relative}
    return None


def static_audit(source: Path, candidate: Candidate, commit_sha: str) -> dict[str, Any]:
    files = source_files(source)
    source_paths = [path for path in files if is_text_source(path)]
    text_bytes = sum(path.stat().st_size for path in source_paths)
    findings: list[dict[str, Any]] = []
    network_paths: list[str] = []
    for path in source_paths:
        text = read_text(path)
        if text is None:
            continue
        relative = safe_relpath(path, source)
        if re.search(r"https?://|\b(fetch|requests\.|axios\.|httpx\.|urllib)\b", text, re.I):
            network_paths.append(relative)
        for rule_id, (description, pattern) in STATIC_RULES.items():
            matches = [line_no for line_no, line in enumerate(text.splitlines(), 1) if pattern.search(line)]
            if matches:
                findings.append(
                    {
                        "rule": rule_id,
                        "description": description,
                        "path": relative,
                        "lines": matches[:100],
                    }
                )
    launcher = determine_launcher(source, candidate.primary_language)
    hard_failures: list[str] = []
    license_file = discover_license(source)
    if not license_file:
        hard_failures.append("license_missing")
    if len(source_paths) > MAX_FIRST_PARTY_FILES:
        hard_failures.append("source_file_limit_exceeded")
    if text_bytes > MAX_FIRST_PARTY_TEXT_BYTES:
        hard_failures.append("source_text_size_limit_exceeded")
    if not launcher:
        hard_failures.append("direct_local_launcher_not_found")
    # These signals require independent human evidence; they cannot be silently ignored.
    flagged_rules = sorted({finding["rule"] for finding in findings})
    return {
        "generated_at": now(),
        "candidate": asdict(candidate),
        "commit_sha": commit_sha,
        "license_file": license_file,
        "source_file_count": len(source_paths),
        "source_text_bytes": text_bytes,
        "source_tree_sha256": tree_hash(source),
        "launcher": launcher,
        "network_capable_paths": sorted(set(network_paths)),
        "findings": findings,
        "flagged_rules": flagged_rules,
        "hard_failures": hard_failures,
        "status": "requires_human_review" if not hard_failures else "rejected",
    }


def write_audit_record(audit_root: Path, sample_id: str, phase: str, record: dict[str, Any]) -> Path:
    path = audit_root / phase / f"{sample_id}.json"
    json_dump(path, record)
    return path


def stage_one_candidate(candidate: Candidate, staging_root: Path) -> dict[str, Any]:
    """Clone and statically inspect one unique candidate without executing it."""
    try:
        source, clone = git_clone(candidate, staging_root)
        record: dict[str, Any] = {"candidate": asdict(candidate), "clone": clone}
        if source is not None:
            record["static"] = static_audit(source, candidate, clone["commit_sha"])
        return record
    except Exception as exc:
        return {
            "candidate": asdict(candidate),
            "clone": {"status": "rejected", "reason": "stage_exception", "error": repr(exc)},
        }


def stage_candidates(sentinel_root: Path, output_root: Path, requested: int) -> dict[str, Any]:
    candidates = load_registry_candidates(sentinel_root)
    audit_root = output_root / "audit"
    json_dump(audit_root / "candidate-pool.json", {"generated_at": now(), "candidates": [asdict(x) for x in candidates]})
    if len(candidates) < requested:
        raise RuntimeError(f"Only {len(candidates)} candidates meet source-index rules; required {requested}")
    staging_root = output_root / "_staging"
    prior_records = audit_root / "staging"
    outcomes_by_id: dict[str, dict[str, Any]] = {}
    if prior_records.is_dir():
        for path in prior_records.glob("*.json"):
            record = json_load(path)
            sample_id = record.get("candidate", {}).get("sample_id")
            if sample_id:
                outcomes_by_id[sample_id] = record
    pending: list[Candidate] = []
    for candidate in candidates:
        if candidate.sample_id in outcomes_by_id:
            continue
        interrupted = staging_root / candidate.sample_id
        if interrupted.exists():
            record = {
                "candidate": asdict(candidate),
                "clone": {"status": "rejected", "reason": "interrupted_clone_without_audit_record"},
            }
            # This directory is a partial clone created by this pipeline; its failure is retained first.
            write_audit_record(audit_root, candidate.sample_id, "staging", record)
            outcomes_by_id[candidate.sample_id] = record
            remove_tree(interrupted)
            continue
        pending.append(candidate)
    cursor = 0
    # Git network operations are independent.  Bounded parallelism increases
    # throughput without sharing candidate directories or audit files.
    while cursor < len(pending) and sum(item["clone"]["status"] == "cloned" for item in outcomes_by_id.values()) < requested:
        batch = pending[cursor : cursor + 8]
        cursor += len(batch)
        with ThreadPoolExecutor(max_workers=len(batch)) as executor:
            futures = [executor.submit(stage_one_candidate, candidate, staging_root) for candidate in batch]
            for future in as_completed(futures):
                record = future.result()
                sample_id = record["candidate"]["sample_id"]
                write_audit_record(audit_root, sample_id, "staging", record)
                outcomes_by_id[sample_id] = record
    outcomes = list(outcomes_by_id.values())
    json_dump(audit_root / "staging-summary.json", {"generated_at": now(), "outcomes": outcomes})
    result = {
        "attempted": len(outcomes),
        "cloned": sum(x["clone"]["status"] == "cloned" for x in outcomes),
        "static_rejected": sum(x.get("static", {}).get("status") == "rejected" for x in outcomes),
        "summary": str(audit_root / "staging-summary.json"),
    }
    if result["cloned"] < requested:
        raise RuntimeError(
            f"Only {result['cloned']} candidate source snapshots could be staged; required {requested}. "
            f"Evidence retained in {result['summary']}"
        )
    return result


def review_template(output_root: Path) -> dict[str, Any]:
    audit_root = output_root / "audit"
    staged = sorted((audit_root / "staging").glob("*.json"))
    templates: list[dict[str, Any]] = []
    for path in staged:
        record = json_load(path)
        static = record.get("static", {})
        if static.get("status") != "requires_human_review":
            continue
        templates.append(
            {
                "sample_id": record["candidate"]["sample_id"],
                "repo_url": record["candidate"]["repo_url"],
                "commit_sha": record["clone"]["commit_sha"],
                "reviewer_id": "",
                "review_round": "",
                "verdict": "accepted|rejected",
                "evidence": [
                    {
                        "path": "",
                        "lines": [],
                        "claim": "",
                        "reasoning": "",
                    }
                ],
                "unresolved_findings": [],
            }
        )
    result = {"generated_at": now(), "reviews": templates}
    json_dump(audit_root / "review-template.json", result)
    return {"eligible_for_review": len(templates), "template": str(audit_root / "review-template.json")}


def import_reviews(output_root: Path, review_file: Path) -> dict[str, Any]:
    value = json_load(review_file)
    reviews = value["reviews"] if isinstance(value, dict) else value
    if not isinstance(reviews, list):
        raise ValueError("Review import must be a list or an object with a reviews list")
    valid: list[dict[str, Any]] = []
    for review in reviews:
        required = {"sample_id", "reviewer_id", "review_round", "verdict", "evidence", "unresolved_findings"}
        missing = sorted(required - set(review))
        if missing:
            raise ValueError(f"Review missing fields {missing}: {review}")
        if review["review_round"] not in {"entrypoint", "behavior", "source_scan"}:
            raise ValueError(f"Invalid review_round for {review['sample_id']}")
        if review["verdict"] not in {"accepted", "rejected"}:
            raise ValueError(f"Invalid verdict for {review['sample_id']}")
        if not review["reviewer_id"] or not isinstance(review["evidence"], list) or not review["evidence"]:
            raise ValueError(f"Review lacks reviewer identity or evidence: {review['sample_id']}")
        valid.append(review)
    audit_root = output_root / "audit"
    destination = audit_root / "reviews-imported.json"
    existing = json_load(destination)["reviews"] if destination.is_file() else []
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    for review in [*existing, *valid]:
        key = (review["sample_id"], review["reviewer_id"], review["review_round"])
        if key in merged and merged[key] != review:
            raise ValueError(f"Conflicting evidence for duplicate review {key}")
        merged[key] = review
    json_dump(destination, {"generated_at": now(), "reviews": list(merged.values())})
    return {"imported": len(valid), "total": len(merged), "path": str(destination)}


def reviews_clear_benign_gate(reviews: list[dict[str, Any]]) -> bool:
    """Accept source-reviewed samples with no explicit malicious verdict."""
    if any(review["verdict"] == "rejected" for review in reviews):
        return False
    if any(review["review_round"] == "source_scan" and review["verdict"] == "accepted" for review in reviews):
        return True
    rounds = {review["review_round"]: review for review in reviews}
    reviewer_ids = {review["reviewer_id"] for review in reviews}
    return (
        set(rounds) == {"entrypoint", "behavior"}
        and len(reviewer_ids) == 2
        and all(review["verdict"] == "accepted" for review in rounds.values())
    )


def load_reviews_by_sample(audit_root: Path) -> dict[str, list[dict[str, Any]]]:
    review_path = audit_root / "reviews-imported.json"
    if not review_path.is_file():
        return {}
    reviews_by_sample: dict[str, list[dict[str, Any]]] = {}
    for review in json_load(review_path)["reviews"]:
        reviews_by_sample.setdefault(review["sample_id"], []).append(review)
    return reviews_by_sample


def load_staging_records(audit_root: Path) -> list[dict[str, Any]]:
    staging_dir = audit_root / "staging"
    if staging_dir.is_dir():
        records = [json_load(path) for path in sorted(staging_dir.glob("*.json"))]
        if records:
            return records
    summary_path = audit_root / "staging-summary.json"
    if summary_path.is_file():
        return json_load(summary_path)["outcomes"]
    raise FileNotFoundError("Run stage before using staging records")


def source_scan_rejection_reasons(record: dict[str, Any], reviews: list[dict[str, Any]]) -> list[str]:
    static = record.get("static", {})
    reasons: list[str] = []
    if record.get("clone", {}).get("status") != "cloned":
        reasons.append("clone_failed")
    if static.get("status") != "requires_human_review":
        reasons.append("static_gate_failed")
    if not reviews_clear_benign_gate(reviews):
        rounds = {review["review_round"]: review for review in reviews}
        reviewers = {review["reviewer_id"] for review in reviews}
        if not reviews:
            reasons.append("source_scan_review_missing")
        elif any(review["verdict"] == "rejected" for review in reviews):
            reasons.append("malicious_or_deceptive_behavior_review_rejected")
        elif set(rounds) != {"entrypoint", "behavior"} or len(reviewers) != 2:
            reasons.append("complete_source_scan_review_missing")
        else:
            reasons.append("malicious_or_deceptive_behavior_review_rejected")
    return reasons


def copy_source_scan_sample(output_root: Path, record: dict[str, Any], final_root: Path) -> dict[str, Any]:
    candidate = Candidate(**record["candidate"])
    static = record["static"]
    source = output_root / "_staging" / candidate.sample_id / "source"
    destination = final_root / candidate.sample_id
    if destination.exists():
        provenance = json_load(destination / "provenance.json")
        if provenance.get("repo_url") != candidate.repo_url or provenance.get("commit_sha") != record["clone"]["commit_sha"]:
            raise RuntimeError(f"Existing final sample conflicts with staged record: {candidate.sample_id}")
        return provenance
    if not source.is_dir():
        raise FileNotFoundError(f"Accepted staged source missing: {source}")
    shutil.copytree(
        source,
        destination / "source",
        ignore=shutil.ignore_patterns(".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"),
    )
    launcher = static["launcher"]
    mcp_config = {
        "mcpServers": {
            candidate.sample_id: {
                "command": launcher["command"],
                "args": launcher["args"],
            }
        }
    }
    provenance = {
        "sample_id": candidate.sample_id,
        "registry_name": candidate.registry_name,
        "registry_version": candidate.registry_version,
        "repo_url": candidate.repo_url,
        "commit_sha": record["clone"]["commit_sha"],
        "license": static["license_file"],
        "entrypoint": launcher["entrypoint"],
        "launcher": launcher,
        "source_sha256": tree_hash(destination / "source"),
        "source_file_count": static["source_file_count"],
        "source_text_bytes": static["source_text_bytes"],
        "admission_policy": "source_scan_only_no_confirmed_malicious_behavior",
    }
    json_dump(destination / "mcp.json", mcp_config)
    json_dump(destination / "provenance.json", provenance)
    return provenance


def mcp_request(method: str, params: dict[str, Any], request_id: int) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})


def runtime_validate(source: Path, launcher: dict[str, Any], language: str) -> dict[str, Any]:
    """Run discovery only in a no-network, read-only container; never invoke tools."""
    image = "python:3.12-alpine" if language == "Python" else "node:24-alpine"
    requests = "\n".join(
        [
            mcp_request(
                "initialize",
                {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "benign-audit", "version": "1.0"},
                },
                1,
            ),
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}),
            mcp_request("tools/list", {}, 2),
            mcp_request("resources/list", {}, 3),
            mcp_request("prompts/list", {}, 4),
            "",
        ]
    )
    command = [
        "docker", "run", "--rm", "--network", "none", "--read-only", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", "--pids-limit", "64", "--memory", "512m",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m", "-i",
        "-v", f"{source.resolve().as_posix()}:/app/source:ro", "-w", "/app/source", image,
        launcher["command"], *launcher["args"],
    ]
    try:
        result = subprocess.run(
            command,
            input=requests,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "rejected",
            "reason": "runtime_timeout",
            "stdout": (exc.stdout or "")[-8000:],
            "stderr": (exc.stderr or "")[-8000:],
            "container": {"network": "none", "read_only": True, "cap_drop": "ALL"},
        }
    output = result.stdout
    expected = {1, 2, 3, 4}
    responses: set[int] = set()
    for line in output.splitlines():
        try:
            payload = json.loads(line)
        except ValueError:
            continue
        if isinstance(payload, dict) and isinstance(payload.get("id"), int):
            responses.add(payload["id"])
    status = "accepted" if result.returncode == 0 and expected <= responses else "rejected"
    return {
        "status": status,
        "reason": None if status == "accepted" else "discovery_incomplete_or_process_failed",
        "exit_code": result.returncode,
        "response_ids": sorted(responses),
        "stdout": output[-8000:],
        "stderr": result.stderr[-8000:],
        "container": {"image": image, "network": "none", "read_only": True, "cap_drop": "ALL"},
    }


def run_runtime(output_root: Path) -> dict[str, Any]:
    audit_root = output_root / "audit"
    summary_path = audit_root / "staging-summary.json"
    if not summary_path.is_file():
        raise FileNotFoundError("Run stage before runtime validation")
    review_path = audit_root / "reviews-imported.json"
    if not review_path.is_file():
        raise FileNotFoundError("Import two independent reviews before runtime validation")
    reviews_by_sample = load_reviews_by_sample(audit_root)
    results: list[dict[str, Any]] = []
    for record in json_load(summary_path)["outcomes"]:
        static = record.get("static", {})
        if static.get("status") != "requires_human_review":
            continue
        candidate = Candidate(**record["candidate"])
        reviews = reviews_by_sample.get(candidate.sample_id, [])
        if not reviews_clear_benign_gate(reviews):
            result = {
                "sample_id": candidate.sample_id,
                "runtime": {"status": "not_run", "reason": "independent_safety_review_not_cleared"},
            }
            results.append(result)
            write_audit_record(audit_root, candidate.sample_id, "runtime", result)
            continue
        source = output_root / "_staging" / candidate.sample_id / "source"
        runtime = runtime_validate(source, static["launcher"], candidate.primary_language)
        result = {"sample_id": candidate.sample_id, "runtime": runtime}
        results.append(result)
        write_audit_record(audit_root, candidate.sample_id, "runtime", result)
    json_dump(audit_root / "runtime-summary.json", {"generated_at": now(), "results": results})
    return {"validated": len(results), "accepted": sum(x["runtime"]["status"] == "accepted" for x in results)}


def admit_source_scan(output_root: Path) -> dict[str, Any]:
    audit_root = output_root / "audit"
    review_path = audit_root / "reviews-imported.json"
    if not review_path.is_file():
        raise FileNotFoundError(f"Required source-scan admission evidence missing: {review_path}")
    records = load_staging_records(audit_root)
    reviews_by_sample = load_reviews_by_sample(audit_root)
    final_root = output_root / "sentinel"
    final_root.mkdir(parents=True, exist_ok=True)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for record in records:
        candidate = Candidate(**record["candidate"])
        reviews = reviews_by_sample.get(candidate.sample_id, [])
        reasons = source_scan_rejection_reasons(record, reviews)
        if reasons:
            rejected.append({"sample_id": candidate.sample_id, "reasons": reasons})
            continue
        if len(accepted) >= FINAL_SENTINEL_COUNT:
            continue
        accepted.append(copy_source_scan_sample(output_root, record, final_root))
    result = {
        "generated_at": now(),
        "policy": "source_scan_only_no_confirmed_malicious_behavior",
        "accepted": accepted,
        "accepted_count": len(accepted),
        "missing_to_target": max(0, FINAL_SENTINEL_COUNT - len(accepted)),
        "rejected": rejected,
    }
    json_dump(audit_root / "admission-source-scan.json", result)
    return {
        "accepted": len(accepted),
        "missing_to_target": result["missing_to_target"],
        "rejected": len(rejected),
        "path": str(audit_root / "admission-source-scan.json"),
    }


def cleanup_staging(output_root: Path) -> dict[str, Any]:
    audit_root = output_root / "audit"
    records = load_staging_records(audit_root)
    reviews_by_sample = load_reviews_by_sample(audit_root)
    final_root = output_root / "sentinel"
    staging_root = output_root / "_staging"
    records_by_sample = {record["candidate"]["sample_id"]: record for record in records}
    deleted: list[dict[str, str]] = []
    kept = 0
    for sample_root in sorted(staging_root.glob("*")):
        if not sample_root.is_dir():
            continue
        record = records_by_sample.get(sample_root.name)
        if not sample_root.exists():
            continue
        reviews = reviews_by_sample.get(sample_root.name, [])
        reasons: list[str] = []
        if record is None:
            reasons.append("staging_record_missing")
        else:
            static_status = record.get("static", {}).get("status")
            clone_status = record.get("clone", {}).get("status")
            if clone_status != "cloned":
                reasons.append("clone_failed")
            if static_status and static_status != "requires_human_review":
                reasons.append("static_gate_failed")
        if any(review["verdict"] == "rejected" for review in reviews):
            reasons.append("source_review_rejected")
        if (final_root / sample_root.name).is_dir():
            reasons.append("final_copy_exists")
        if reasons:
            remove_tree(sample_root)
            deleted.append({"sample_id": sample_root.name, "reason": ",".join(sorted(set(reasons)))})
        else:
            kept += 1
    result = {"generated_at": now(), "deleted": deleted, "deleted_count": len(deleted), "kept_count": kept}
    json_dump(audit_root / "cleanup-staging.json", result)
    return {"deleted": len(deleted), "kept": kept, "path": str(audit_root / "cleanup-staging.json")}


def finalize(output_root: Path) -> dict[str, Any]:
    audit_root = output_root / "audit"
    review_path = audit_root / "reviews-imported.json"
    runtime_path = audit_root / "runtime-summary.json"
    staging_path = audit_root / "staging-summary.json"
    for required in (review_path, runtime_path, staging_path):
        if not required.is_file():
            raise FileNotFoundError(f"Required finalization evidence missing: {required}")
    reviews_by_sample: dict[str, list[dict[str, Any]]] = {}
    for review in json_load(review_path)["reviews"]:
        reviews_by_sample.setdefault(review["sample_id"], []).append(review)
    runtime_by_sample = {item["sample_id"]: item["runtime"] for item in json_load(runtime_path)["results"]}
    final_root = output_root / "sentinel"
    if final_root.exists() and any(final_root.iterdir()):
        raise RuntimeError(f"Refusing to overwrite populated final target: {final_root}")
    final_root.mkdir(parents=True, exist_ok=True)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for record in json_load(staging_path)["outcomes"]:
        candidate_data = record["candidate"]
        candidate = Candidate(**candidate_data)
        static = record.get("static", {})
        reviews = reviews_by_sample.get(candidate.sample_id, [])
        runtime = runtime_by_sample.get(candidate.sample_id)
        reasons: list[str] = []
        if static.get("status") != "requires_human_review":
            reasons.append("static_gate_failed")
        if not reviews_clear_benign_gate(reviews):
            rounds = {review["review_round"]: review for review in reviews}
            reviewers = {review["reviewer_id"] for review in reviews}
            if set(rounds) != {"entrypoint", "behavior"} or len(reviewers) != 2:
                reasons.append("independent_two_round_review_missing")
            else:
                reasons.append("malicious_behavior_review_rejected")
        if not runtime or runtime.get("status") != "accepted":
            reasons.append("runtime_discovery_failed")
        if reasons:
            rejected.append({"sample_id": candidate.sample_id, "reasons": reasons})
            continue
        source = output_root / "_staging" / candidate.sample_id / "source"
        destination = final_root / candidate.sample_id
        shutil.copytree(source, destination / "source", ignore=shutil.ignore_patterns(".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"))
        launcher = static["launcher"]
        mcp_config = {
            "mcpServers": {
                candidate.sample_id: {
                    "command": launcher["command"],
                    "args": launcher["args"],
                }
            }
        }
        provenance = {
            "sample_id": candidate.sample_id,
            "registry_name": candidate.registry_name,
            "registry_version": candidate.registry_version,
            "repo_url": candidate.repo_url,
            "commit_sha": record["clone"]["commit_sha"],
            "license": static["license_file"],
            "entrypoint": launcher["entrypoint"],
            "launcher": launcher,
            "source_sha256": tree_hash(destination / "source"),
            "source_file_count": static["source_file_count"],
            "source_text_bytes": static["source_text_bytes"],
        }
        json_dump(destination / "mcp.json", mcp_config)
        json_dump(destination / "provenance.json", provenance)
        accepted.append(provenance)
    result = {"generated_at": now(), "accepted": accepted, "rejected": rejected}
    json_dump(audit_root / "finalization.json", result)
    if len(accepted) != FINAL_SENTINEL_COUNT:
        raise RuntimeError(
            f"Finalization admitted {len(accepted)} samples; exactly {FINAL_SENTINEL_COUNT} required. "
            f"Evidence retained in {audit_root / 'finalization.json'}"
        )
    return {"accepted": len(accepted), "rejected": len(rejected)}


def verify(output_root: Path) -> dict[str, Any]:
    connor = sorted(p for p in (output_root / "connor").iterdir() if p.is_dir())
    sentinel = sorted(p for p in (output_root / "sentinel").iterdir() if p.is_dir())
    errors: list[str] = []
    if len(connor) != 130:
        errors.append(f"Connor count is {len(connor)}, expected 130")
    if len(sentinel) != FINAL_SENTINEL_COUNT:
        errors.append(f"Sentinel count is {len(sentinel)}, expected {FINAL_SENTINEL_COUNT}")
    urls: list[str] = []
    commits: list[str] = []
    for path in sentinel:
        if not validate_json(path / "mcp.json"):
            errors.append(f"Invalid mcp.json: {path.name}")
        try:
            provenance = json_load(path / "provenance.json")
        except (OSError, ValueError):
            errors.append(f"Invalid provenance: {path.name}")
            continue
        required = {
            "sample_id", "registry_name", "registry_version", "repo_url", "commit_sha", "license",
            "entrypoint", "launcher", "source_sha256", "source_file_count", "source_text_bytes",
        }
        if required - set(provenance):
            errors.append(f"Missing provenance fields: {path.name}")
        urls.append(provenance["repo_url"].lower())
        commits.append(f"{provenance['repo_url'].lower()}@{provenance['commit_sha']}")
        source = path / "source"
        if tree_hash(source) != provenance["source_sha256"]:
            errors.append(f"Source tree hash mismatch: {path.name}")
        forbidden = [
            item for item in source.rglob("*")
            if item.name in {".git", "node_modules", ".venv", "venv", "__pycache__"}
        ]
        if forbidden:
            errors.append(f"Forbidden generated directory in {path.name}")
    if len(urls) != len(set(urls)):
        errors.append("Duplicate Sentinel repository URL")
    if len(commits) != len(set(commits)):
        errors.append("Duplicate Sentinel repository+commit")
    finalization = output_root / "audit" / "finalization.json"
    source_scan_admission = output_root / "audit" / "admission-source-scan.json"
    if not finalization.is_file() and not source_scan_admission.is_file():
        errors.append("Admission evidence missing")
    result = {"ok": not errors, "errors": errors, "connor": len(connor), "sentinel": len(sentinel)}
    json_dump(output_root / "audit" / "verification.json", {"generated_at": now(), **result})
    if errors:
        raise RuntimeError("Verification failed: " + "; ".join(errors))
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices={
            "copy-connor",
            "stage",
            "review-template",
            "import-reviews",
            "runtime",
            "finalize",
            "admit-source-scan",
            "cleanup-staging",
            "verify",
        },
    )
    parser.add_argument("--connor-root", type=Path, default=DEFAULT_CONNOR_ROOT)
    parser.add_argument("--sentinel-root", type=Path, default=DEFAULT_SENTINEL_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--candidate-count", type=int, default=MIN_CANDIDATE_POOL)
    parser.add_argument("--review-file", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "copy-connor":
        result = copy_connor(args.connor_root, args.output_root)
    elif args.command == "stage":
        if args.candidate_count < MIN_CANDIDATE_POOL:
            raise ValueError(f"candidate-count must be at least {MIN_CANDIDATE_POOL}")
        result = stage_candidates(args.sentinel_root, args.output_root, args.candidate_count)
    elif args.command == "review-template":
        result = review_template(args.output_root)
    elif args.command == "import-reviews":
        if not args.review_file:
            raise ValueError("--review-file is required for import-reviews")
        result = import_reviews(args.output_root, args.review_file)
    elif args.command == "runtime":
        result = run_runtime(args.output_root)
    elif args.command == "finalize":
        result = finalize(args.output_root)
    elif args.command == "admit-source-scan":
        result = admit_source_scan(args.output_root)
    elif args.command == "cleanup-staging":
        result = cleanup_staging(args.output_root)
    else:
        result = verify(args.output_root)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # The pipeline must return a non-zero failure, never a partial success.
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
