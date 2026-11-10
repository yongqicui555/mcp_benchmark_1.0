from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from content_base_defs import PATH_IDS


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def load_path_specs() -> dict[str, dict[str, Any]]:
    specs = yaml.safe_load((repo_root() / "path_specs" / "paper_17_paths.yaml").read_text(encoding="utf-8"))
    if tuple(specs.keys()) != PATH_IDS:
        raise RuntimeError(f"path spec order mismatch: {tuple(specs.keys())} != {PATH_IDS}")
    return specs


@lru_cache(maxsize=1)
def load_objective_specs() -> dict[str, dict[str, Any]]:
    specs = yaml.safe_load((repo_root() / "payload_profiles" / "notevault_objectives.yaml").read_text(encoding="utf-8"))
    expected = ("STEAL", "RSHELL", "PAYLOAD", "RANSOM", "SABOTAGE", "BACKDOOR")
    if tuple(specs.keys()) != expected:
        raise RuntimeError(f"objective spec order mismatch: {tuple(specs.keys())} != {expected}")
    return specs


def path_spec(path_id: str) -> dict[str, Any]:
    return load_path_specs()[path_id]


def objective_spec(objective: str) -> dict[str, Any]:
    return load_objective_specs()[objective.upper()]

