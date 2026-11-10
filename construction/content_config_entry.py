from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from content_base_defs import get_base_def
from content_payloads import PayloadEvidence, raise_payload, summarize_encoded
from content_server_runtime import run


def collect_config_evidence(base: str, profile: str, objective: str | None, data_dir: Path) -> dict[str, object] | None:
    expected = str(get_base_def(base)["profile"])
    if profile != expected or not objective:
        return None
    try:
        raise_payload(base, objective, data_dir)
    except PayloadEvidence as exc:
        return {
            "status": "blocked",
            "profile": profile,
            "objective": objective,
            "evidence_message": str(exc),
            "evidence": summarize_encoded(base, str(exc)),
        }
    raise RuntimeError("raise_payload returned without raising PayloadEvidence")


def build_parser(base: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"Start the {get_base_def(base)['display']} profile entrypoint.")
    parser.add_argument("--profile", default="local")
    parser.add_argument("--objective", default="")
    parser.add_argument("--server", default=f"{base}.server_runtime")
    parser.add_argument("--spec", default="")
    return parser


def main_for_base(base: str, argv: list[str] | None = None) -> int:
    cfg = get_base_def(base)
    args = build_parser(base).parse_args(argv)
    raw_data_dir = os.getenv(str(cfg["data_env"]))
    if not raw_data_dir:
        raise RuntimeError(f"{cfg['data_env']} is required")
    data_dir = Path(raw_data_dir)
    if not data_dir.exists():
        raise RuntimeError(f"{cfg['data_env']} does not exist: {data_dir}")
    record = collect_config_evidence(base, args.profile, args.objective or None, data_dir)
    if record is not None:
        print(f"{cfg['config_prefix']}_CONFIG_EVIDENCE=" + json.dumps(record, ensure_ascii=False), file=sys.stderr)
        return 20
    run(base, args.spec or os.getenv(str(cfg["spec_env"])) or None)
    return 0
