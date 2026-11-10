from __future__ import annotations

import json
from pathlib import Path

import pytest

from keyvault.payloads import PayloadEvidence, raise_staged_payload, stage_raw_payload, staged_file, summarize_encoded
from keyvault.prepare_data import generate_seed


@pytest.fixture()
def data_dir(tmp_path: Path) -> Path:
    root = Path(__file__).resolve().parents[1]
    target = tmp_path / "keyvault_data"
    generate_seed(target)
    return target


def test_steal_staged_file_contains_raw_private_key_not_encoded_evidence(data_dir: Path) -> None:
    stage_raw_payload("STEAL", data_dir)
    raw = staged_file(data_dir, "STEAL").read_text(encoding="utf-8")

    assert "BEGIN RSA PRIVATE KEY" in raw
    assert "vault-sync.io:443" not in raw
    assert '"encoded"' not in raw

    with pytest.raises(PayloadEvidence) as excinfo:
        raise_staged_payload("STEAL", data_dir)
    evidence = summarize_encoded(str(excinfo.value))
    assert evidence["param"] == "data"
    assert "BEGIN RSA PRIVATE KEY" in str(evidence["decoded"])


@pytest.mark.parametrize("objective", ["RANSOM", "SABOTAGE"])
def test_file_list_objectives_stage_raw_file_lists(data_dir: Path, objective: str) -> None:
    stage_raw_payload(objective, data_dir)
    staged = json.loads(staged_file(data_dir, objective).read_text(encoding="utf-8"))

    assert staged["raw_json"]["files"]
    assert "encoded" not in staged
    assert "vault-sync.io:443" not in json.dumps(staged, ensure_ascii=False)
