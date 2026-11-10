import hashlib
from pathlib import Path

import pytest

from benchmark.tools.catalog import filesystem_root, read_labels, statistics, verify_inventory, within


def test_release_identity_and_gray_subset():
    rows = read_labels()
    assert len({(row["base"], row["mcp_id"]) for row in rows}) == 1025
    result = statistics(rows)
    assert result["malicious"] == 510
    assert result["layers"]["L2"] == 85
    assert result["layers"]["imported_benign"] == 340


def test_inventory_detects_modified_missing_and_unlisted_files(tmp_path):
    sample = tmp_path / "benchmark/mcp_dataset/example/server.py"
    sample.parent.mkdir(parents=True)
    original = b"raise RuntimeError('must never be executed by verification')\n"
    sample.write_bytes(original)
    record = {"path": sample.relative_to(tmp_path).as_posix(), "bytes": len(original), "sha256": hashlib.sha256(original).hexdigest()}
    assert verify_inventory(tmp_path, [record]) == ([], 1)
    sample.write_bytes(b"x" * len(original))
    assert "Checksum mismatch" in verify_inventory(tmp_path, [record])[0][0]
    sample.unlink()
    assert "Missing file" in verify_inventory(tmp_path, [record])[0][0]
    sample.write_bytes(original)
    assert "Unlisted file" in verify_inventory(tmp_path, [])[0][0]


def test_repository_relative_paths_cannot_escape(tmp_path):
    assert within(tmp_path, "benchmark/example") == tmp_path / "benchmark/example"
    with pytest.raises(ValueError):
        within(tmp_path, "../outside")
    with pytest.raises(ValueError):
        within(tmp_path, str(Path(tmp_path).resolve()))


def test_inventory_reads_long_nested_source_paths(tmp_path):
    root = filesystem_root(tmp_path)
    relative = "benchmark/mcp_dataset/" + "/".join(["nested_" + "a" * 70] * 3) + "/data.txt"
    target = root / relative
    target.parent.mkdir(parents=True)
    target.write_bytes(b"fixture")
    record = {"path": relative, "bytes": 7, "sha256": hashlib.sha256(b"fixture").hexdigest()}
    assert verify_inventory(tmp_path, [record]) == ([], 1)
