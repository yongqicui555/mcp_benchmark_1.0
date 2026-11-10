from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


PATH_IDS = (
    "P1",
    "P3",
    "P4",
    "P6",
    "P7",
    "P8",
    "P9",
    "P10",
    "P11",
    "P12",
    "P13",
    "P14",
    "P15",
    "P16",
    "P17",
    "P18",
    "P19",
)

OBJECTIVES = ("STEAL", "RSHELL", "PAYLOAD", "RANSOM", "SABOTAGE", "BACKDOOR")


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
    specs = yaml.safe_load((repo_root() / "payload_profiles" / "devspace_objectives.yaml").read_text(encoding="utf-8"))
    if tuple(specs.keys()) != OBJECTIVES:
        raise RuntimeError(f"objective spec order mismatch: {tuple(specs.keys())} != {OBJECTIVES}")
    return specs

