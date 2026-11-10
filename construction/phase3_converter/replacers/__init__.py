"""Replacer registry — maps objective name to replacer module."""
from __future__ import annotations

from . import steal, rshell, payload, ransom, sabotage, backdoor
from ..config import BaseConfig

_MODULES = {
    "STEAL":    steal,
    "RSHELL":   rshell,
    "PAYLOAD":  payload,
    "RANSOM":   ransom,
    "SABOTAGE": sabotage,
    "BACKDOOR": backdoor,
}


def get_dispatch_body(objective: str, cfg: BaseConfig) -> str:
    """Return the dispatch_sync_report function body for the given objective and base."""
    return _MODULES[objective].get_dispatch_body(cfg)


def get_new_imports(objective: str) -> list[str]:
    """Return additional import lines needed for the given objective."""
    return _MODULES[objective].NEW_IMPORTS


def get_p18_complete_body(objective: str, cfg: BaseConfig) -> str:
    """Return the complete_rotation_context / complete_workspace_context function body for P18 staged path."""
    return _MODULES[objective].get_p18_complete_body(cfg)
