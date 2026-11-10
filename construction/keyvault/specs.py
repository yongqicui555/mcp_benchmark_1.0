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


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def load_path_specs() -> dict[str, dict[str, Any]]:
    path = repo_root() / "path_specs" / "paper_17_paths.yaml"
    specs = yaml.safe_load(path.read_text(encoding="utf-8"))
    if tuple(specs.keys()) != PATH_IDS:
        raise RuntimeError(f"path spec order mismatch: {tuple(specs.keys())} != {PATH_IDS}")
    return specs


@lru_cache(maxsize=1)
def load_objective_specs() -> dict[str, dict[str, Any]]:
    path = repo_root() / "payload_profiles" / "keyvault_objectives.yaml"
    specs = yaml.safe_load(path.read_text(encoding="utf-8"))
    expected = ("STEAL", "RSHELL", "PAYLOAD", "RANSOM", "SABOTAGE", "BACKDOOR")
    if tuple(specs.keys()) != expected:
        raise RuntimeError(f"objective spec order mismatch: {tuple(specs.keys())} != {expected}")
    return specs


def path_spec(path_id: str) -> dict[str, Any]:
    specs = load_path_specs()
    if path_id not in specs:
        raise ValueError(f"unknown path id: {path_id}")
    return specs[path_id]


def model_passes(path_id: str) -> int:
    return int(path_spec(path_id)["model_passes"])


def normalized_path(path_id: str) -> str:
    return str(path_spec(path_id)["normalized_path"])


def objective_spec(objective: str) -> dict[str, Any]:
    normalized = objective.upper()
    specs = load_objective_specs()
    if normalized not in specs:
        raise ValueError(f"unknown objective: {objective}")
    return specs[normalized]
