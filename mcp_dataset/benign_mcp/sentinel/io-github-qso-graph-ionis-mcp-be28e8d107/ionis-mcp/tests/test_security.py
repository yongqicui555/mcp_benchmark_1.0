"""L1 Security tests for ionis-mcp — MCP Security Framework compliance.

Verifies the 10 non-negotiable security guarantees from
planning/MCP-SECURITY-FRAMEWORK.md. These tests scan source code
statically — no runtime, no network, no fixtures needed.

Guarantees tested:
  S1: Credentials in OS keyring only (N/A — ionis-mcp has no credentials)
  S2: Credentials never in logs/tool results/errors
  S3: No command injection surface (no subprocess, no shell=True)
  S4: All external connections HTTPS only
  S5: Rate limiting (structural — NOAA cache TTL)
  S6: Input validation on user strings
  S7: No eval/exec
  S8: No hardcoded secrets
  S9: Read-only database access (sqlite mode=ro)
  S10: No credential leakage in error messages
"""

import ast
import os
import re

SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "ionis_mcp")


def _all_py_sources():
    """Yield all Python source files under SRC_DIR."""
    for root, _, files in os.walk(SRC_DIR):
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(root, f)


# ── S2: No credential logging ───────────────────────────────────────────────

def test_no_print_credentials():
    """S2: No print() calls with credential keywords."""
    pattern = re.compile(
        r'print\s*\(.*?(password|passwd|secret|api_key|token|credential)',
        re.IGNORECASE,
    )
    for path in _all_py_sources():
        with open(path) as fh:
            src = fh.read()
        assert not pattern.search(src), f"Credential print in {path}"


def test_no_logging_credentials():
    """S2: No logging calls with credential keywords."""
    pattern = re.compile(
        r'log(?:ging|ger)?\.\w+\s*\(.*?(password|passwd|secret|api_key|credential)',
        re.IGNORECASE,
    )
    for path in _all_py_sources():
        with open(path) as fh:
            src = fh.read()
        assert not pattern.search(src), f"Credential logging in {path}"


# ── S3: No command injection ─────────────────────────────────────────────────

def test_no_subprocess():
    """S3: No subprocess or shell=True usage."""
    pattern = re.compile(r'\bsubprocess\b|shell\s*=\s*True')
    for path in _all_py_sources():
        with open(path) as fh:
            src = fh.read()
        assert not pattern.search(src), f"subprocess/shell in {path}"


def test_no_os_system():
    """S3: No os.system() or os.popen() calls."""
    pattern = re.compile(r'os\.(system|popen)\s*\(')
    for path in _all_py_sources():
        with open(path) as fh:
            src = fh.read()
        assert not pattern.search(src), f"os.system/popen in {path}"


# ── S4: HTTPS only ──────────────────────────────────────────────────────────

def test_all_urls_https():
    """S4: All hardcoded URLs use HTTPS (except localhost)."""
    pattern = re.compile(r'http://(?!localhost|127\.0\.0\.1)')
    for path in _all_py_sources():
        with open(path) as fh:
            src = fh.read()
        assert not pattern.search(src), f"Non-HTTPS URL in {path}"


# ── S5: Rate limiting ───────────────────────────────────────────────────────

def test_noaa_cache_ttl_exists():
    """S5: NOAA module has a cache TTL to prevent hammering."""
    noaa_path = os.path.join(SRC_DIR, "noaa.py")
    with open(noaa_path) as fh:
        src = fh.read()
    assert "_CACHE_TTL" in src, "NOAA cache TTL not found"
    assert "_cache" in src, "NOAA cache dict not found"


# ── S7: No eval/exec ────────────────────────────────────────────────────────

def test_no_eval_exec():
    """S7: No eval() or exec() in source code."""
    for path in _all_py_sources():
        with open(path) as fh:
            src = fh.read()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in ("eval", "exec"):
                    raise AssertionError(f"eval/exec found in {path}")


# ── S8: No hardcoded secrets ────────────────────────────────────────────────

def test_no_hardcoded_secrets():
    """S8: No hardcoded API keys, passwords, or tokens in source."""
    patterns = [
        re.compile(r'(?:api_key|password|secret|token)\s*=\s*["\'][^"\']{8,}["\']', re.IGNORECASE),
        re.compile(r'sk-[a-zA-Z0-9]{20,}'),  # OpenAI-style keys
        re.compile(r'Bearer\s+[a-zA-Z0-9]{20,}'),
    ]
    for path in _all_py_sources():
        with open(path) as fh:
            for i, line in enumerate(fh, 1):
                if line.lstrip().startswith("#"):
                    continue
                for pat in patterns:
                    assert not pat.search(line), (
                        f"Possible hardcoded secret in {path}:{i}: {line.strip()[:80]}"
                    )


# ── S9: Read-only database ──────────────────────────────────────────────────

def test_sqlite_read_only():
    """S9: All SQLite connections use mode=ro (read-only)."""
    db_path = os.path.join(SRC_DIR, "database.py")
    with open(db_path) as fh:
        src = fh.read()
    # Every sqlite3.connect call should use mode=ro
    connect_calls = re.findall(r'sqlite3\.connect\([^)]+\)', src)
    assert connect_calls, "No sqlite3.connect calls found in database.py"
    for call in connect_calls:
        assert "mode=ro" in call, f"SQLite connection without mode=ro: {call}"


# ── S10: Safe error messages ────────────────────────────────────────────────

def test_error_messages_safe():
    """S10: No credential interpolation in error messages."""
    dangerous = re.compile(
        r'\{(password|api_key|secret|creds\.password|creds\.api_key)\}',
        re.IGNORECASE,
    )
    for path in _all_py_sources():
        with open(path) as fh:
            for i, line in enumerate(fh, 1):
                if line.lstrip().startswith("#"):
                    continue
                matches = dangerous.findall(line)
                assert not matches, (
                    f"Credential interpolation in {path}:{i}: {line.strip()}"
                )


# ── S6: Input validation ────────────────────────────────────────────────────

def test_sql_uses_parameterized_queries():
    """S6: All SQL queries use parameterized ? placeholders, not f-strings for values."""
    db_path = os.path.join(SRC_DIR, "database.py")
    with open(db_path) as fh:
        src = fh.read()
    # Check that execute calls use ? params, not direct string interpolation of user values
    # The table names are from a fixed registry (safe), but WHERE values must be parameterized
    dangerous = re.compile(r'execute\([^)]*\{(tx_grid|rx_grid|band|hour|month|source)')
    assert not dangerous.search(src), "User input interpolated directly in SQL query"


def test_grid_validation_exists():
    """S6: Grid validation function exists and rejects bad input."""
    from ionis_mcp.grids import validate_grid

    # Valid grids
    assert validate_grid("DN13") is not None
    assert validate_grid("dn13") is not None
    assert validate_grid("JO51ab") is not None

    # Invalid grids — must return None
    assert validate_grid("") is None
    assert validate_grid("ZZ99") is None  # Z > R in field
    assert validate_grid("AAAA") is None
    assert validate_grid("12AB") is None
    assert validate_grid("'; DROP TABLE--") is None
    assert validate_grid("<script>") is None
