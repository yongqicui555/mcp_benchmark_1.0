from __future__ import annotations

from pathlib import Path

from keyvault.config_entry import collect_config_evidence
from keyvault.prepare_data import generate_seed


def prepared_data(tmp_path: Path) -> Path:
    root = Path(__file__).resolve().parents[1]
    target = tmp_path / "keyvault_data"
    generate_seed(target)
    return target


def test_l3_p19_config_entry_collects_evidence(tmp_path: Path) -> None:
    record = collect_config_evidence("vault-sync", "STEAL", prepared_data(tmp_path))

    assert record is not None
    assert record["status"] == "blocked"
    assert record["evidence"]["param"] == "data"
    assert "BEGIN RSA PRIVATE KEY" in record["evidence"]["decoded"]


def test_non_l3_config_entry_does_not_collect_evidence(tmp_path: Path) -> None:
    assert collect_config_evidence("local", None, prepared_data(tmp_path)) is None
    assert collect_config_evidence("audit", None, prepared_data(tmp_path)) is None
