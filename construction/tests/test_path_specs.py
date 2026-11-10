from __future__ import annotations

from keyvault.specs import PATH_IDS, load_path_specs


def test_paper_17_path_set_is_complete_and_merged() -> None:
    specs = load_path_specs()

    assert tuple(specs) == PATH_IDS
    assert "P2" not in specs
    assert "P5" not in specs
    assert len(specs) == 17


def test_direct_paths_are_fixed_zero_model_passes() -> None:
    specs = load_path_specs()

    for path_id in ("P17", "P18", "P19"):
        assert specs[path_id]["direct"] is True
        assert specs[path_id]["model_passes"] == 0


def test_builtin_paths_are_only_the_paper_builtin_sinks() -> None:
    specs = load_path_specs()
    builtin_paths = {path_id for path_id, spec in specs.items() if spec["sink"] == "Builtin"}

    assert builtin_paths == {"P1", "P8", "P13", "P16"}
    assert {path_id for path_id, spec in specs.items() if spec["builtin_expected"]} == builtin_paths


def test_injection_points_follow_paper_table_after_merges() -> None:
    specs = load_path_specs()

    expected = {
        "P1": ["TD", "AS"],
        "P3": ["TD", "TSC"],
        "P4": ["TD", "AS", "TSC"],
        "P6": ["TD", "RSC"],
        "P7": ["TR", "TSC"],
        "P8": ["TR"],
        "P9": ["TR", "TSC"],
        "P10": ["TR", "RSC"],
        "P11": ["TD", "RR", "TSC"],
        "P12": ["TD", "RR", "TSC"],
        "P13": ["TD", "RR"],
        "P14": ["TD", "TR", "RSC"],
        "P15": ["TD", "TR", "TSC"],
        "P16": ["TD", "TR"],
        "P17": ["TSC"],
        "P18": ["TSC"],
        "P19": ["CONFIG"],
    }
    assert {path_id: spec["injection_points"] for path_id, spec in specs.items()} == expected
