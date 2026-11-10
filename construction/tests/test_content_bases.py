from __future__ import annotations

import json
from pathlib import Path

import pytest

from content_base_defs import BASE_DEFS, OBJECTIVES, PATH_IDS, get_base_def
from content_payloads import PayloadEvidence, raise_staged_payload, stage_raw_payload, staged_file, summarize_encoded
from content_prepare import copy_seed, generate_seed
from host_builtins import BuiltinContext, execute_builtin
from scripts.content_construct import all_specs, render_clean_server, write_clean_variant, write_ground_truth


CONTENT_BASES = ("notevault", "docforge", "scaffoldkit")


@pytest.mark.parametrize("base", CONTENT_BASES)
def test_content_base_specs_have_required_distribution(base: str) -> None:
    specs = all_specs(base)

    assert len(specs) == 137
    assert sum(1 for spec in specs if spec["layer"] == "L0") == 1
    assert sum(1 for spec in specs if spec["layer"] == "L1") == 17
    assert sum(1 for spec in specs if spec["layer"] == "L2") == 17
    assert sum(1 for spec in specs if spec["layer"] == "L3") == 102
    assert {spec["path"] for spec in specs if spec["path"]} == set(PATH_IDS)
    assert {spec["objective"] for spec in specs if spec["objective"]} == set(OBJECTIVES)


@pytest.mark.parametrize("base", CONTENT_BASES)
def test_content_clean_server_is_static_and_p19_matches_l0(base: str) -> None:
    l0 = render_clean_server(next(spec for spec in all_specs(base) if spec["variant"] == "L0"))
    p11 = render_clean_server(next(spec for spec in all_specs(base) if spec["variant"] == "L3_P11(STEAL)"))
    p19 = render_clean_server(next(spec for spec in all_specs(base) if spec["variant"] == "L3_P19(STEAL)"))

    compile(p11, f"{base}-server.py", "exec")
    assert "from mcp.server.fastmcp import FastMCP" in p11
    assert "variant_spec" not in p11
    assert "SPEC" not in p11
    assert "raise_by_objective" not in p11
    assert "dispatch_objective" not in p11
    assert "collect_report" not in p11
    assert "STEAL" not in p11
    assert p19 == l0


@pytest.mark.parametrize("base", CONTENT_BASES)
def test_content_clean_variant_and_ground_truth_are_physically_separate(tmp_path: Path, base: str) -> None:
    cfg = get_base_def(base)
    seed_dir = tmp_path / f"{base}_seed"
    clean_root = tmp_path / "clean_mcp" / base
    generate_seed(base, seed_dir, force=True)

    specs = all_specs(base)
    write_clean_variant(clean_root, seed_dir, next(spec for spec in specs if spec["variant"] == "L3_P11(STEAL)"), force=True)
    label_root = write_ground_truth(tmp_path, clean_root, specs, base)

    clean_dir = clean_root / "L3_P11(STEAL)"
    assert (clean_dir / "server.py").exists()
    assert (clean_dir / str(cfg["data_dir"])).is_dir()
    assert not (clean_dir / "variant_spec.json").exists()
    assert not (clean_dir / "labels.jsonl").exists()
    assert (label_root / "labels.jsonl").exists()


@pytest.mark.parametrize("base", CONTENT_BASES)
def test_content_p18_stages_raw_parameters_before_encoded_raise(tmp_path: Path, base: str) -> None:
    cfg = get_base_def(base)
    data_dir = tmp_path / str(cfg["data_dir"])
    generate_seed(base, tmp_path / "seed", force=True)
    copy_seed(tmp_path / "seed", data_dir, force=True)

    stage_raw_payload(base, "STEAL", data_dir)
    staged = json.loads(staged_file(data_dir, "STEAL").read_text(encoding="utf-8"))

    assert staged["param"] == "data"
    assert "raw_json" in staged
    assert "encoded" not in staged
    assert str(cfg["endpoint"]) not in json.dumps(staged, ensure_ascii=False)

    with pytest.raises(PayloadEvidence) as excinfo:
        raise_staged_payload(base, "STEAL", data_dir)
    evidence = summarize_encoded(base, str(excinfo.value))
    assert evidence["param"] == "data"
    assert str(cfg["steal_expected"]) in evidence["decoded"]


@pytest.mark.parametrize("base", CONTENT_BASES)
def test_content_builtin_command_blocks_and_collects_base_evidence(tmp_path: Path, base: str) -> None:
    cfg = get_base_def(base)
    variant_dir = tmp_path / "variant"
    data_dir = variant_dir / str(cfg["data_dir"])
    generate_seed(base, tmp_path / "seed", force=True)
    copy_seed(tmp_path / "seed", data_dir, force=True)
    ctx = BuiltinContext(repo_root=Path(__file__).resolve().parents[1], variant_dir=variant_dir, spec={"base": base, "objective": "STEAL"})

    result = execute_builtin("builtin_run_command", {"command": cfg["builtin_commands"]["STEAL"]}, ctx)

    assert result["blocked"] is True
    assert result["executed"] is False
    assert result["network_access"] is False
    assert str(cfg["endpoint"]) in result["evidence_message"]
    assert str(cfg["steal_expected"]) in summarize_encoded(base, result["evidence_message"])["decoded"]


def test_content_base_definitions_cover_expected_three_bases() -> None:
    assert set(BASE_DEFS) == set(CONTENT_BASES)
