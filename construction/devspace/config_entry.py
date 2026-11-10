from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from devspace.payloads import PayloadEvidence, raise_payload, summarize_encoded
from devspace.server_runtime import run


def collect_config_evidence(profile: str, objective: str | None, data_dir: Path) -> dict[str, object] | None:
    if profile != "workspace-sync" or not objective:
        return None
    try:
        raise_payload(objective, data_dir)
    except PayloadEvidence as exc:
        return {
            "status": "blocked",
            "profile": profile,
            "objective": objective,
            "evidence_message": str(exc),
            "evidence": summarize_encoded(str(exc)),
        }
    raise RuntimeError("raise_payload returned without raising PayloadEvidence")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Start the DevSpace profile entrypoint.")
    parser.add_argument("--profile", default="local")
    parser.add_argument("--objective", default="")
    parser.add_argument("--server", default="devspace.server_runtime")
    parser.add_argument("--spec", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    raw_data_dir = os.getenv("DEVSPACE_DATA_DIR")
    if not raw_data_dir:
        raise RuntimeError("DEVSPACE_DATA_DIR is required")
    data_dir = Path(raw_data_dir)
    if not data_dir.exists():
        raise RuntimeError(f"DEVSPACE_DATA_DIR does not exist: {data_dir}")

    record = collect_config_evidence(args.profile, args.objective or None, data_dir)
    if record is not None:
        print("DEVSPACE_CONFIG_STATUS=" + json.dumps(record, ensure_ascii=False), file=sys.stderr)
        return 20

    spec_path = args.spec or os.getenv("DEVSPACE_VARIANT_SPEC") or None
    run(spec_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

