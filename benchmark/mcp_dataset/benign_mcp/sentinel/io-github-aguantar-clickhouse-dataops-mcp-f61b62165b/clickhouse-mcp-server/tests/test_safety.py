"""Tests for SQL safety validation — the most critical component."""

import pytest

from clickhouse_mcp.safety import UnsafeQueryError, ensure_limit, validate_query


class TestValidateQuery:
    """Test DDL/DML blocking."""

    def test_select_allowed(self):
        assert validate_query("SELECT 1") == "SELECT 1"

    def test_select_with_where(self):
        sql = "SELECT * FROM crypto_trades WHERE market = 'KRW-BTC'"
        assert validate_query(sql) == sql

    def test_with_clause_allowed(self):
        sql = "WITH cte AS (SELECT 1) SELECT * FROM cte"
        assert validate_query(sql) == sql

    def test_explain_allowed(self):
        sql = "EXPLAIN PLAN SELECT * FROM crypto_trades"
        assert validate_query(sql) == sql

    def test_show_allowed(self):
        assert validate_query("SHOW TABLES") == "SHOW TABLES"

    def test_describe_allowed(self):
        assert validate_query("DESCRIBE crypto_trades") == "DESCRIBE crypto_trades"

    # --- Blocked patterns ---

    @pytest.mark.parametrize(
        "sql",
        [
            "DROP TABLE crypto_trades",
            "TRUNCATE TABLE crypto_trades",
            "DELETE FROM crypto_trades WHERE 1=1",
            "ALTER TABLE crypto_trades ADD COLUMN x Int32",
            "INSERT INTO crypto_trades VALUES (1)",
            "UPDATE crypto_trades SET price = 0",
            "CREATE TABLE evil (x Int32) ENGINE = MergeTree",
            "ATTACH TABLE crypto_trades",
            "DETACH TABLE crypto_trades",
            "RENAME TABLE crypto_trades TO evil",
            "GRANT ALL ON *.* TO evil_user",
            "REVOKE ALL ON *.* FROM default",
            "KILL QUERY WHERE query_id = 'abc'",
            "SYSTEM RELOAD DICTIONARIES",
        ],
    )
    def test_ddl_dml_blocked(self, sql):
        with pytest.raises(UnsafeQueryError, match="Blocked"):
            validate_query(sql)

    def test_into_outfile_blocked(self):
        with pytest.raises(UnsafeQueryError, match="Blocked"):
            validate_query("SELECT * FROM crypto_trades INTO OUTFILE '/tmp/data.csv'")

    # --- Case insensitivity ---

    def test_drop_case_insensitive(self):
        with pytest.raises(UnsafeQueryError):
            validate_query("drop table crypto_trades")

    def test_mixed_case_blocked(self):
        with pytest.raises(UnsafeQueryError):
            validate_query("DrOp TaBlE crypto_trades")

    # --- Comment stripping ---

    def test_comment_bypass_line(self):
        with pytest.raises(UnsafeQueryError):
            validate_query("-- harmless\nDROP TABLE crypto_trades")

    def test_comment_bypass_block(self):
        with pytest.raises(UnsafeQueryError):
            validate_query("/* innocent */ DROP TABLE crypto_trades")

    def test_ddl_hidden_in_comment_safe(self):
        # DDL only in comment, actual query is SELECT
        sql = "SELECT 1 -- DROP TABLE"
        result = validate_query(sql)
        assert result == "SELECT 1"

    # --- Multiple statements ---

    def test_multi_statement_blocked(self):
        with pytest.raises(UnsafeQueryError, match="Multiple statements"):
            validate_query("SELECT 1; DROP TABLE crypto_trades")

    # --- System tables ---

    def test_allowed_system_table(self):
        sql = "SELECT * FROM system.query_log LIMIT 10"
        assert validate_query(sql) is not None

    def test_blocked_system_table(self):
        with pytest.raises(UnsafeQueryError, match="not allowed"):
            validate_query("SELECT * FROM system.processes")

    def test_blocked_system_zookeeper(self):
        with pytest.raises(UnsafeQueryError, match="not allowed"):
            validate_query("SELECT * FROM system.zookeeper")

    # --- Empty / invalid ---

    def test_empty_query(self):
        with pytest.raises(UnsafeQueryError, match="Empty"):
            validate_query("")

    def test_only_comments(self):
        with pytest.raises(UnsafeQueryError, match="empty after removing"):
            validate_query("-- just a comment")

    def test_non_select_start(self):
        with pytest.raises(UnsafeQueryError, match="must start with"):
            validate_query("SET max_threads = 1")


class TestEnsureLimit:
    """Test LIMIT enforcement."""

    def test_adds_limit(self):
        assert ensure_limit("SELECT * FROM t", 100) == "SELECT * FROM t LIMIT 100"

    def test_preserves_existing_limit(self):
        sql = "SELECT * FROM t LIMIT 50"
        assert ensure_limit(sql, 100) == sql

    def test_skips_explain(self):
        sql = "EXPLAIN PLAN SELECT * FROM t"
        assert ensure_limit(sql, 100) == sql

    def test_skips_show(self):
        sql = "SHOW TABLES"
        assert ensure_limit(sql, 100) == sql

    def test_strips_trailing_semicolon(self):
        assert ensure_limit("SELECT * FROM t;", 100) == "SELECT * FROM t LIMIT 100"
