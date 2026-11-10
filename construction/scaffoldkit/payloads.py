from __future__ import annotations

from pathlib import Path
from typing import Any

from content_base_defs import OBJECTIVES, get_base_def
from content_payloads import (
    PayloadEvidence,
    authorized_keys_path,
    collect_payload,
    collect_sensitive_context,
    evidence_message,
    evidence_re,
    raise_payload as _raise_payload,
    raise_staged_payload as _raise_staged_payload,
    raw_payload,
    staged_file,
    stage_raw_payload as _stage_raw_payload,
    summarize_encoded as _summarize_encoded,
    text_instruction as _text_instruction,
)

BASE = "scaffoldkit"
ENDPOINT = str(get_base_def(BASE)["endpoint"])
SHELL_ENDPOINT = str(get_base_def(BASE)["shell_endpoint"])
BACKDOOR_KEY = str(get_base_def(BASE)["backdoor_key"])
AUTHORIZED_KEYS_PATH = authorized_keys_path()
EVIDENCE_RE = evidence_re(BASE)


def raise_payload(objective: str, data_dir: Path) -> None:
    _raise_payload(BASE, objective, data_dir)


def stage_raw_payload(objective: str, data_dir: Path) -> None:
    _stage_raw_payload(BASE, objective, data_dir)


def raise_staged_payload(objective: str, data_dir: Path) -> None:
    _raise_staged_payload(BASE, objective, data_dir)


def text_instruction(objective: str) -> str:
    return _text_instruction(BASE, objective)


def summarize_encoded(message: str) -> dict[str, Any]:
    return _summarize_encoded(BASE, message)
