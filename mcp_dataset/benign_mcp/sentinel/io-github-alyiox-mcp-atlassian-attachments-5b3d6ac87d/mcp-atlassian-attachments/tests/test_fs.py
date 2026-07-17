from __future__ import annotations

import httpx
import pytest

from mcp_atlassian_attachments.fs import (
    resolve_output_path,
    sanitize_filename,
    stream_to_file,
)


class TestSanitizeFilename:
    def test_passes_through_normal_name(self):
        assert sanitize_filename("report.pdf") == "report.pdf"

    def test_replaces_slash(self):
        assert "/" not in sanitize_filename("a/b.txt")

    def test_replaces_backslash(self):
        assert "\\" not in sanitize_filename("a\\b.txt")

    def test_replaces_special_chars(self):
        result = sanitize_filename('file:*?"<>|.txt')
        for ch in ':*?"<>|':
            assert ch not in result

    def test_strips_leading_dots(self):
        assert not sanitize_filename("...hidden").startswith(".")

    def test_empty_becomes_attachment(self):
        assert sanitize_filename("") == "attachment"

    def test_only_dots_becomes_attachment(self):
        assert sanitize_filename("...") == "attachment"


class TestResolveOutputPath:
    def test_creates_dir_if_missing(self, tmp_path):
        target_dir = tmp_path / "new" / "nested"
        path = resolve_output_path(str(target_dir), "file.txt")
        assert target_dir.is_dir()
        assert path.name == "file.txt"

    def test_path_inside_dir(self, tmp_path):
        path = resolve_output_path(str(tmp_path), "test.png")
        assert str(path).startswith(str(tmp_path))

    def test_rejects_path_traversal(self, tmp_path):
        with pytest.raises(ValueError, match="escape"):
            resolve_output_path(str(tmp_path), "../../etc/passwd")

    def test_rejects_absolute_filename(self, tmp_path):
        with pytest.raises((ValueError, OSError)):
            resolve_output_path(str(tmp_path), "/etc/passwd")

    def test_accepts_filename_with_hyphens_and_dots(self, tmp_path):
        path = resolve_output_path(str(tmp_path), "snipaste-20260421-103126-933.png")
        assert path.parent == tmp_path
        assert path.name == "snipaste-20260421-103126-933.png"


class TestStreamToFile:
    def _make_response(self, content: bytes, status: int = 200) -> httpx.Response:
        return httpx.Response(status, content=content)

    def test_writes_content(self, tmp_path):
        path = tmp_path / "out.bin"
        resp = self._make_response(b"hello world")
        n = stream_to_file(resp, path, expected_size=None, overwrite=False)
        assert n == 11
        assert path.read_bytes() == b"hello world"

    def test_verifies_size(self, tmp_path):
        path = tmp_path / "out.bin"
        resp = self._make_response(b"hello")
        with pytest.raises(ValueError, match="mismatch"):
            stream_to_file(resp, path, expected_size=100, overwrite=False)
        assert not path.exists()

    def test_raises_on_existing_file_no_overwrite(self, tmp_path):
        path = tmp_path / "out.bin"
        path.write_bytes(b"existing")
        resp = self._make_response(b"new")
        with pytest.raises(FileExistsError):
            stream_to_file(resp, path, expected_size=None, overwrite=False)

    def test_overwrites_when_flag_true(self, tmp_path):
        path = tmp_path / "out.bin"
        path.write_bytes(b"old")
        resp = self._make_response(b"new content")
        stream_to_file(resp, path, expected_size=None, overwrite=True)
        assert path.read_bytes() == b"new content"
