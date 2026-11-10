import importlib.util
import json
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_benign_dataset.py"
SPEC = importlib.util.spec_from_file_location("build_benign_dataset", MODULE_PATH)
builder = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


def test_stable_sample_id_is_repo_sensitive():
    assert builder.stable_sample_id("example/mcp", "https://github.com/a/mcp") != builder.stable_sample_id(
        "example/mcp", "https://github.com/b/mcp"
    )


def test_python_launcher_requires_direct_file(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "server.py").write_text("print('no runtime execution in this test')\n", encoding="utf-8")
    assert builder.determine_launcher(source, "Python") == {
        "command": "python",
        "args": ["/app/source/server.py"],
        "entrypoint": "server.py",
    }


def test_static_audit_rejects_missing_license_and_records_risk(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "server.py").write_text("import os\nos.system('whoami')\n", encoding="utf-8")
    candidate = builder.Candidate(
        sample_id="sample", registry_name="example/mcp", registry_version="1.0.0",
        repo_url="https://github.com/example/mcp", primary_language="Python", package={},
        requires_api_key=False, required_env_vars="", enrichment_status="success",
    )
    result = builder.static_audit(source, candidate, "a" * 40)
    assert result["status"] == "rejected"
    assert "license_missing" in result["hard_failures"]
    assert "process_execution" in result["flagged_rules"]


def test_mcp_config_rejects_shell_derived_launcher_by_construction(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "package.json").write_text(json.dumps({"bin": "server.ts"}), encoding="utf-8")
    (source / "server.ts").write_text("export {};", encoding="utf-8")
    assert builder.determine_launcher(source, "TypeScript") is None


def test_benign_review_gate_records_observations_without_rejecting():
    reviews = [
        {"review_round": "entrypoint", "reviewer_id": "one", "verdict": "accepted", "unresolved_findings": ["version drift"]},
        {"review_round": "behavior", "reviewer_id": "two", "verdict": "accepted", "unresolved_findings": ["documented filesystem write"]},
    ]
    assert builder.reviews_clear_benign_gate(reviews)
    reviews[1]["verdict"] = "rejected"
    assert not builder.reviews_clear_benign_gate(reviews)


def test_source_scan_review_can_admit_without_runtime_or_double_review():
    reviews = [
        {
            "review_round": "source_scan",
            "reviewer_id": "one",
            "verdict": "accepted",
            "unresolved_findings": ["transparent remote API"],
        }
    ]
    assert builder.reviews_clear_benign_gate(reviews)
    reviews.append(
        {
            "review_round": "source_scan",
            "reviewer_id": "two",
            "verdict": "rejected",
            "unresolved_findings": ["hidden credential exfiltration"],
        }
    )
    assert not builder.reviews_clear_benign_gate(reviews)


def test_source_scan_admission_requires_static_and_two_review_rounds():
    record = {
        "candidate": {"sample_id": "sample"},
        "clone": {"status": "cloned"},
        "static": {"status": "requires_human_review"},
    }
    reviews = [
        {"review_round": "entrypoint", "reviewer_id": "one", "verdict": "accepted", "unresolved_findings": ["transparent network"]},
        {"review_round": "behavior", "reviewer_id": "two", "verdict": "accepted", "unresolved_findings": ["transparent file read"]},
    ]
    assert builder.source_scan_rejection_reasons(record, reviews) == []
    assert builder.source_scan_rejection_reasons(record, reviews[:1]) == [
        "complete_source_scan_review_missing"
    ]
    record["static"]["status"] = "rejected"
    assert "static_gate_failed" in builder.source_scan_rejection_reasons(record, reviews)


def test_source_scan_admission_accepts_single_complete_source_scan():
    record = {
        "candidate": {"sample_id": "sample"},
        "clone": {"status": "cloned"},
        "static": {"status": "requires_human_review"},
    }
    reviews = [
        {
            "review_round": "source_scan",
            "reviewer_id": "scanner",
            "verdict": "accepted",
            "evidence": [{"path": "source/server.py", "lines": [1], "claim": "No malicious behavior found."}],
            "unresolved_findings": ["transparent network API"],
        }
    ]
    assert builder.reviews_clear_benign_gate(reviews)
    assert builder.source_scan_rejection_reasons(record, reviews) == []
    reviews[0]["verdict"] = "rejected"
    assert "malicious_or_deceptive_behavior_review_rejected" in builder.source_scan_rejection_reasons(record, reviews)


def test_cleanup_staging_removes_only_disqualified_snapshots(tmp_path):
    output = tmp_path / "benign_mcp"
    audit = output / "audit"
    staging = output / "_staging"
    for sample in ("bad", "todo"):
        (staging / sample / "source").mkdir(parents=True)
    outcomes = [
        {
            "candidate": {
                "sample_id": "bad",
                "registry_name": "bad",
                "registry_version": "1.0.0",
                "repo_url": "https://github.com/example/bad",
                "primary_language": "Python",
                "package": {},
                "requires_api_key": False,
                "required_env_vars": "",
                "enrichment_status": "success",
            },
            "clone": {"status": "cloned"},
            "static": {"status": "rejected"},
        },
        {
            "candidate": {
                "sample_id": "todo",
                "registry_name": "todo",
                "registry_version": "1.0.0",
                "repo_url": "https://github.com/example/todo",
                "primary_language": "Python",
                "package": {},
                "requires_api_key": False,
                "required_env_vars": "",
                "enrichment_status": "success",
            },
            "clone": {"status": "cloned"},
            "static": {"status": "requires_human_review"},
        },
    ]
    builder.json_dump(audit / "staging-summary.json", {"outcomes": outcomes})
    result = builder.cleanup_staging(output)
    assert result["deleted"] == 1
    assert not (staging / "bad").exists()
    assert (staging / "todo").exists()
