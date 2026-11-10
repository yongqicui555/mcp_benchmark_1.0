"""SQL safety layer — blocks DDL/DML and enforces read-only access."""

import re

BLOCKED_PATTERNS = [
    re.compile(
        r"\b(DROP|TRUNCATE|DELETE|ALTER|INSERT|UPDATE|CREATE|ATTACH|DETACH|RENAME|GRANT|REVOKE)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bKILL\b", re.IGNORECASE),
    re.compile(r"\bSYSTEM\s+(RELOAD|FLUSH|STOP|START|RESTART|DROP|SYNC)\b", re.IGNORECASE),
    re.compile(r"INTO\s+OUTFILE", re.IGNORECASE),
]

ALLOWED_SYSTEM_TABLES = {
    "system.query_log",
    "system.parts",
    "system.columns",
    "system.tables",
    "system.databases",
    "system.merges",
    "system.mutations",
    "system.disks",
}

_COMMENT_LINE = re.compile(r"--.*$", re.MULTILINE)
_COMMENT_BLOCK = re.compile(r"/\*.*?\*/", re.DOTALL)
_SYSTEM_TABLE = re.compile(r"\bsystem\.(\w+)", re.IGNORECASE)


class UnsafeQueryError(Exception):
    pass


def _strip_comments(sql: str) -> str:
    sql = _COMMENT_BLOCK.sub("", sql)
    sql = _COMMENT_LINE.sub("", sql)
    return sql


def validate_query(sql: str) -> str:
    """Validate and return the cleaned SQL. Raises UnsafeQueryError if blocked."""
    if not sql or not sql.strip():
        raise UnsafeQueryError("Empty query")

    cleaned = _strip_comments(sql).strip()

    if not cleaned:
        raise UnsafeQueryError("Query is empty after removing comments")

    # Block multiple statements
    statements = [s.strip() for s in cleaned.split(";") if s.strip()]
    if len(statements) > 1:
        raise UnsafeQueryError(
            "Multiple statements not allowed. Send one query at a time."
        )

    # Block DDL/DML patterns
    for pattern in BLOCKED_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            raise UnsafeQueryError(
                f"Blocked: '{match.group()}' is not allowed. Only SELECT queries are permitted."
            )

    # Check system table access
    for m in _SYSTEM_TABLE.finditer(cleaned):
        full_name = f"system.{m.group(1)}"
        if full_name not in ALLOWED_SYSTEM_TABLES:
            raise UnsafeQueryError(
                f"Access to '{full_name}' is not allowed. "
                f"Allowed: {', '.join(sorted(ALLOWED_SYSTEM_TABLES))}"
            )

    # Must start with SELECT, EXPLAIN, SHOW, DESCRIBE, EXISTS, or WITH
    first_word = cleaned.split()[0].upper()
    if first_word not in ("SELECT", "EXPLAIN", "SHOW", "DESCRIBE", "DESC", "EXISTS", "WITH"):
        raise UnsafeQueryError(
            f"Query must start with SELECT, EXPLAIN, SHOW, DESCRIBE, or WITH. Got: '{first_word}'"
        )

    return cleaned


def ensure_limit(sql: str, max_rows: int) -> str:
    """Append LIMIT if not already present (skip for EXPLAIN/SHOW/DESCRIBE)."""
    upper = sql.strip().upper()
    if upper.startswith(("EXPLAIN", "SHOW", "DESCRIBE", "DESC")):
        return sql

    if re.search(r"\bLIMIT\s+\d+", upper):
        return sql

    return f"{sql.rstrip().rstrip(';')} LIMIT {max_rows}"
