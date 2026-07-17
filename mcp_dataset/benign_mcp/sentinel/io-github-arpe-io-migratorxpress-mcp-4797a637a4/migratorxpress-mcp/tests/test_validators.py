"""Tests for validators module."""

import pytest
from pydantic import ValidationError

from src.validators import (
    TaskType,
    SourceDatabaseType,
    TargetDatabaseType,
    MigrationDbMode,
    LoadMode,
    FkMode,
    LogLevel,
    MigrationParams,
)


class TestTaskType:
    """Tests for TaskType enum."""

    def test_all_8_task_types(self):
        """Test that there are exactly 8 task types."""
        assert len(TaskType) == 8

    def test_task_types_exist(self):
        """Test all task type values exist."""
        assert TaskType("translate") == TaskType.TRANSLATE
        assert TaskType("create") == TaskType.CREATE
        assert TaskType("transfer") == TaskType.TRANSFER
        assert TaskType("diff") == TaskType.DIFF
        assert TaskType("copy_pk") == TaskType.COPY_PK
        assert TaskType("copy_ak") == TaskType.COPY_AK
        assert TaskType("copy_fk") == TaskType.COPY_FK
        assert TaskType("all") == TaskType.ALL

    def test_invalid_task_type(self):
        """Test that invalid task type raises ValueError."""
        with pytest.raises(ValueError):
            TaskType("invalid")


class TestSourceDatabaseType:
    """Tests for SourceDatabaseType enum."""

    def test_all_4_source_types(self):
        """Test that there are exactly 4 source database types."""
        assert len(SourceDatabaseType) == 4

    def test_source_types_exist(self):
        """Test all source database types exist."""
        assert SourceDatabaseType("oracle") == SourceDatabaseType.ORACLE
        assert SourceDatabaseType("postgresql") == SourceDatabaseType.POSTGRESQL
        assert SourceDatabaseType("sqlserver") == SourceDatabaseType.SQLSERVER
        assert SourceDatabaseType("netezza") == SourceDatabaseType.NETEZZA


class TestTargetDatabaseType:
    """Tests for TargetDatabaseType enum."""

    def test_all_4_target_types(self):
        """Test that there are exactly 4 target database types."""
        assert len(TargetDatabaseType) == 4

    def test_target_types_exist(self):
        """Test all target database types exist."""
        assert TargetDatabaseType("postgresql") == TargetDatabaseType.POSTGRESQL
        assert TargetDatabaseType("sqlserver") == TargetDatabaseType.SQLSERVER
        assert TargetDatabaseType("mysql") == TargetDatabaseType.MYSQL
        assert TargetDatabaseType("oracle") == TargetDatabaseType.ORACLE


class TestOtherEnums:
    """Tests for other enum types."""

    def test_all_3_migration_db_modes(self):
        """Test all 3 migration DB mode values exist."""
        assert len(MigrationDbMode) == 3
        assert MigrationDbMode("preserve") == MigrationDbMode.PRESERVE
        assert MigrationDbMode("truncate") == MigrationDbMode.TRUNCATE
        assert MigrationDbMode("drop") == MigrationDbMode.DROP

    def test_all_2_load_modes(self):
        """Test all 2 load mode values exist."""
        assert len(LoadMode) == 2
        assert LoadMode("truncate") == LoadMode.TRUNCATE
        assert LoadMode("append") == LoadMode.APPEND

    def test_all_3_fk_modes(self):
        """Test all 3 FK mode values exist."""
        assert len(FkMode) == 3
        assert FkMode("trusted") == FkMode.TRUSTED
        assert FkMode("untrusted") == FkMode.UNTRUSTED
        assert FkMode("disabled") == FkMode.DISABLED

    def test_all_5_log_levels(self):
        """Test all 5 log level values exist."""
        assert len(LogLevel) == 5
        assert LogLevel("DEBUG") == LogLevel.DEBUG
        assert LogLevel("INFO") == LogLevel.INFO
        assert LogLevel("WARNING") == LogLevel.WARNING
        assert LogLevel("ERROR") == LogLevel.ERROR
        assert LogLevel("CRITICAL") == LogLevel.CRITICAL


class TestMigrationParams:
    """Tests for MigrationParams model."""

    def _minimal_params(self, **overrides):
        """Helper to create minimal valid params."""
        base = {
            "auth_file": "auth.json",
            "source_db_auth_id": "source_db",
            "source_db_name": "mydb",
            "target_db_auth_id": "target_db",
            "target_db_name": "targetdb",
            "migration_db_auth_id": "migration_db",
        }
        base.update(overrides)
        return base

    def test_valid_minimal(self):
        """Test valid minimal parameters (6 required fields only)."""
        params = MigrationParams(**self._minimal_params())
        assert params.auth_file == "auth.json"
        assert params.source_db_auth_id == "source_db"
        assert params.source_db_name == "mydb"
        assert params.target_db_auth_id == "target_db"
        assert params.target_db_name == "targetdb"
        assert params.migration_db_auth_id == "migration_db"

    def test_auth_file_required(self):
        """Test that auth_file is required."""
        with pytest.raises(ValidationError):
            MigrationParams(
                source_db_auth_id="src",
                source_db_name="db",
                target_db_auth_id="tgt",
                target_db_name="db",
                migration_db_auth_id="mig",
            )

    def test_source_db_auth_id_required(self):
        """Test that source_db_auth_id is required."""
        with pytest.raises(ValidationError):
            MigrationParams(
                auth_file="auth.json",
                source_db_name="db",
                target_db_auth_id="tgt",
                target_db_name="db",
                migration_db_auth_id="mig",
            )

    def test_target_db_auth_id_required(self):
        """Test that target_db_auth_id is required."""
        with pytest.raises(ValidationError):
            MigrationParams(
                auth_file="auth.json",
                source_db_auth_id="src",
                source_db_name="db",
                target_db_name="db",
                migration_db_auth_id="mig",
            )

    def test_migration_db_auth_id_required(self):
        """Test that migration_db_auth_id is required."""
        with pytest.raises(ValidationError):
            MigrationParams(
                auth_file="auth.json",
                source_db_auth_id="src",
                source_db_name="db",
                target_db_auth_id="tgt",
                target_db_name="db",
            )

    def test_valid_with_all_params(self):
        """Test valid parameters with all optional fields."""
        params = MigrationParams(
            **self._minimal_params(
                source_schema_name="dbo",
                target_schema_name="public",
                task_list=["translate", "create", "transfer"],
                resume="run-123",
                fasttransfer_dir_path="/opt/fasttransfer",
                fasttransfer_p=4,
                ft_large_table_th=100000,
                n_jobs=2,
                cci_threshold=500000,
                aci_threshold=100000,
                migration_db_mode="truncate",
                compute_nbrows="true",
                drop_tables_if_exists="false",
                load_mode="truncate",
                include_tables="orders*",
                exclude_tables="*_tmp",
                min_rows=100,
                max_rows=1000000,
                forced_int_id_prefixes=["ID_", "PK_"],
                forced_int_id_suffixes=["_ID", "_PK"],
                profiling_sample_pc=0.1,
                p_query=0.05,
                min_sample_pc_profile=0.01,
                force=True,
                basic_diff=True,
                without_xid=True,
                fk_mode="trusted",
                log_level="DEBUG",
                log_dir="/tmp/logs",
                no_banner=True,
                no_progress=True,
                quiet_ft=True,
                license="ABC-123-DEF",
            )
        )
        assert params.source_schema_name == "dbo"
        assert params.n_jobs == 2
        assert params.force is True
        assert params.fk_mode == FkMode.TRUSTED

    def test_task_list_valid(self):
        """Test valid task list."""
        params = MigrationParams(
            **self._minimal_params(task_list=["translate", "create", "transfer"])
        )
        assert params.task_list == ["translate", "create", "transfer"]

    def test_task_list_invalid_task(self):
        """Test that invalid task in task_list raises error."""
        with pytest.raises(ValidationError) as exc_info:
            MigrationParams(**self._minimal_params(task_list=["translate", "invalid"]))
        errors = exc_info.value.errors()
        assert any("invalid" in str(e).lower() for e in errors)

    def test_task_list_all_alone(self):
        """Test that 'all' alone is valid."""
        params = MigrationParams(**self._minimal_params(task_list=["all"]))
        assert params.task_list == ["all"]

    def test_task_list_all_with_others(self):
        """Test that 'all' cannot be combined with other tasks."""
        with pytest.raises(ValidationError) as exc_info:
            MigrationParams(**self._minimal_params(task_list=["all", "translate"]))
        errors = exc_info.value.errors()
        assert any("all" in str(e).lower() for e in errors)

    def test_string_boolean_valid_true(self):
        """Test valid string-boolean 'true'."""
        params = MigrationParams(**self._minimal_params(compute_nbrows="true"))
        assert params.compute_nbrows == "true"

    def test_string_boolean_valid_false(self):
        """Test valid string-boolean 'false'."""
        params = MigrationParams(**self._minimal_params(drop_tables_if_exists="false"))
        assert params.drop_tables_if_exists == "false"

    def test_string_boolean_invalid(self):
        """Test that invalid string-boolean raises error."""
        with pytest.raises(ValidationError) as exc_info:
            MigrationParams(**self._minimal_params(compute_nbrows="yes"))
        errors = exc_info.value.errors()
        assert any(
            "true" in str(e).lower() or "false" in str(e).lower() for e in errors
        )

    def test_license_mutual_exclusivity(self):
        """Test that license and license_file are mutually exclusive."""
        with pytest.raises(ValidationError) as exc_info:
            MigrationParams(
                **self._minimal_params(
                    license="ABC-123",
                    license_file="/path/to/license",
                )
            )
        errors = exc_info.value.errors()
        assert any("mutually exclusive" in str(e).lower() for e in errors)

    def test_license_alone_valid(self):
        """Test that license alone is valid."""
        params = MigrationParams(**self._minimal_params(license="ABC-123"))
        assert params.license == "ABC-123"

    def test_license_file_alone_valid(self):
        """Test that license_file alone is valid."""
        params = MigrationParams(
            **self._minimal_params(license_file="/path/to/license")
        )
        assert params.license_file == "/path/to/license"

    def test_default_boolean_flags_are_false(self):
        """Test that all default boolean flags are False."""
        params = MigrationParams(**self._minimal_params())
        assert params.force is False
        assert params.basic_diff is False
        assert params.without_xid is False
        assert params.no_banner is False
        assert params.no_progress is False
        assert params.quiet_ft is False
