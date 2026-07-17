"""Tests for MigratorXpress command builder."""

from pathlib import Path
from unittest.mock import Mock, patch
import subprocess

import pytest

from src.migratorxpress import (
    CommandBuilder,
    MigratorXpressError,
    get_supported_capabilities,
    suggest_workflow,
)
from src.validators import MigrationParams
from src.version import MigratorXpressVersion


@pytest.fixture
def mock_binary(tmp_path):
    """Create a mock MigratorXpress binary."""
    binary = tmp_path / "MigratorXpress"
    binary.write_text("#!/bin/bash\necho 'mock binary'")
    binary.chmod(0o755)
    return str(binary)


@pytest.fixture
def command_builder(mock_binary):
    """Create a CommandBuilder with mock binary."""
    with patch("src.migratorxpress.VersionDetector") as MockDetector:
        mock_detector = MockDetector.return_value
        mock_detector.detect.return_value = MigratorXpressVersion(0, 6, 24)
        mock_detector.capabilities = Mock()
        mock_detector.capabilities.source_databases = frozenset(
            ["oracle", "postgresql", "sqlserver", "netezza"]
        )
        mock_detector.capabilities.target_databases = frozenset(
            ["postgresql", "sqlserver"]
        )
        mock_detector.capabilities.migration_db_types = frozenset(["sqlserver"])
        mock_detector.capabilities.tasks = frozenset(
            [
                "translate",
                "create",
                "transfer",
                "diff",
                "copy_pk",
                "copy_ak",
                "copy_fk",
                "all",
            ]
        )
        mock_detector.capabilities.fk_modes = frozenset(
            ["trusted", "untrusted", "disabled"]
        )
        mock_detector.capabilities.migration_db_modes = frozenset(
            ["preserve", "truncate", "drop"]
        )
        mock_detector.capabilities.load_modes = frozenset(["truncate", "append"])
        mock_detector.capabilities.supports_no_banner = True
        mock_detector.capabilities.supports_version_flag = True
        mock_detector.capabilities.supports_fasttransfer = True
        mock_detector.capabilities.supports_license = True
        builder = CommandBuilder(mock_binary)
    return builder


def _minimal_params(**overrides):
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


class TestCommandBuilder:
    """Tests for CommandBuilder class."""

    def test_init_with_valid_binary(self, mock_binary):
        """Test initialization with valid binary."""
        with patch("src.migratorxpress.VersionDetector"):
            builder = CommandBuilder(mock_binary)
        assert builder.binary_path == Path(mock_binary)

    def test_init_with_nonexistent_binary_sets_preview_only(self):
        """Test initialization with nonexistent binary enters preview-only mode."""
        builder = CommandBuilder("/nonexistent/path/MigratorXpress")
        assert builder._preview_only is True

    def test_init_with_non_executable_binary_sets_preview_only(self, tmp_path):
        """Test initialization with non-executable binary enters preview-only mode."""
        binary = tmp_path / "MigratorXpress"
        binary.write_text("not executable")
        binary.chmod(0o644)

        builder = CommandBuilder(str(binary))
        assert builder._preview_only is True

    def test_preview_only_execute_command_raises(self):
        """Test that execute_command raises in preview-only mode."""
        builder = CommandBuilder("/nonexistent/path/MigratorXpress")
        assert builder._preview_only is True

        with pytest.raises(MigratorXpressError) as exc_info:
            builder.execute_command(["test"])
        assert "Execution requires" in str(exc_info.value)
        assert "https://arpe.io" in str(exc_info.value)

    def test_preview_only_get_version(self):
        """Test that get_version works in preview-only mode with fallback capabilities."""
        builder = CommandBuilder("/nonexistent/path/MigratorXpress")
        assert builder._preview_only is True

        info = builder.get_version()
        assert info["preview_only"] is True
        assert "Set binary path" in info["message"]
        assert info["version"] is None
        assert info["detected"] is False
        assert "capabilities" in info
        # Should have capabilities from the latest registry entry
        assert len(info["capabilities"]["tasks"]) > 0
        assert len(info["capabilities"]["source_databases"]) > 0

    def test_preview_only_build_command_works(self):
        """Test that build_command works in preview-only mode."""
        builder = CommandBuilder("/nonexistent/path/MigratorXpress")
        assert builder._preview_only is True

        params = MigrationParams(**_minimal_params())
        command = builder.build_command(params)
        assert command[0] == "/nonexistent/path/MigratorXpress"
        assert "-a" in command

    def test_build_command_minimal(self, command_builder):
        """Test building command with minimal (6 required) params only."""
        params = MigrationParams(**_minimal_params())
        command = command_builder.build_command(params)

        assert command[0] == str(command_builder.binary_path)
        assert "-a" in command
        idx = command.index("-a")
        assert command[idx + 1] == "auth.json"
        assert "--source_db_auth_id" in command
        assert "--source_db_name" in command
        assert "--target_db_auth_id" in command
        assert "--target_db_name" in command
        assert "--migration_db_auth_id" in command

    def test_no_subcommand_token(self, command_builder):
        """Test that command has no subcommand — command[1] should be '-a'."""
        params = MigrationParams(**_minimal_params())
        command = command_builder.build_command(params)

        # command[0] is binary path, command[1] should be '-a' (not a subcommand)
        assert command[1] == "-a"

    def test_task_list_nargs_plus(self, command_builder):
        """Test task_list nargs='+' — flag once, then each value as separate element."""
        params = MigrationParams(
            **_minimal_params(task_list=["translate", "create", "transfer"])
        )
        command = command_builder.build_command(params)

        idx = command.index("--task_list")
        assert command[idx + 1] == "translate"
        assert command[idx + 2] == "create"
        assert command[idx + 3] == "transfer"

    def test_forced_int_id_prefixes_nargs_plus(self, command_builder):
        """Test forced_int_id_prefixes nargs='+' handling."""
        params = MigrationParams(
            **_minimal_params(forced_int_id_prefixes=["ID_", "PK_"])
        )
        command = command_builder.build_command(params)

        idx = command.index("--forced_int_id_prefixes")
        assert command[idx + 1] == "ID_"
        assert command[idx + 2] == "PK_"

    def test_forced_int_id_suffixes_nargs_plus(self, command_builder):
        """Test forced_int_id_suffixes nargs='+' handling."""
        params = MigrationParams(
            **_minimal_params(forced_int_id_suffixes=["_ID", "_PK"])
        )
        command = command_builder.build_command(params)

        idx = command.index("--forced_int_id_suffixes")
        assert command[idx + 1] == "_ID"
        assert command[idx + 2] == "_PK"

    def test_resume_flag(self, command_builder):
        """Test resume flag: -r RUN_ID."""
        params = MigrationParams(**_minimal_params(resume="run-123"))
        command = command_builder.build_command(params)

        assert "-r" in command
        idx = command.index("-r")
        assert command[idx + 1] == "run-123"

    def test_string_boolean_params(self, command_builder):
        """Test string-boolean params: --compute_nbrows true."""
        params = MigrationParams(
            **_minimal_params(compute_nbrows="true", drop_tables_if_exists="false")
        )
        command = command_builder.build_command(params)

        idx = command.index("--compute_nbrows")
        assert command[idx + 1] == "true"
        idx = command.index("--drop_tables_if_exists")
        assert command[idx + 1] == "false"

    def test_boolean_flags(self, command_builder):
        """Test boolean flags: -f, --basic_diff, --without_xid, --no_banner, --no_progress, --quiet_ft."""
        params = MigrationParams(
            **_minimal_params(
                force=True,
                basic_diff=True,
                without_xid=True,
                no_banner=True,
                no_progress=True,
                quiet_ft=True,
            )
        )
        command = command_builder.build_command(params)

        assert "-f" in command
        assert "--basic_diff" in command
        assert "--without_xid" in command
        assert "--no_banner" in command
        assert "--no_progress" in command
        assert "--quiet_ft" in command

    def test_all_params_integration(self, command_builder):
        """Test building command with all optional parameters."""
        params = MigrationParams(
            **_minimal_params(
                source_schema_name="dbo",
                target_schema_name="public",
                task_list=["translate", "create"],
                resume="run-123",
                fasttransfer_dir_path="/opt/ft",
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
                forced_int_id_prefixes=["ID_"],
                forced_int_id_suffixes=["_ID"],
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
        command = command_builder.build_command(params)

        assert "--source_schema_name" in command
        assert "--target_schema_name" in command
        assert "--task_list" in command
        assert "-r" in command
        assert "--fasttransfer_dir_path" in command
        assert "-p" in command
        assert "--ft_large_table_th" in command
        assert "--n_jobs" in command
        assert "--cci_threshold" in command
        assert "--aci_threshold" in command
        assert "--migration_db_mode" in command
        assert "--compute_nbrows" in command
        assert "--drop_tables_if_exists" in command
        assert "--load_mode" in command
        assert "-i" in command
        assert "-e" in command
        assert "-min" in command
        assert "-max" in command
        assert "--forced_int_id_prefixes" in command
        assert "--forced_int_id_suffixes" in command
        assert "--profiling_sample_pc" in command
        assert "--p_query" in command
        assert "--min_sample_pc_profile" in command
        assert "-f" in command
        assert "--basic_diff" in command
        assert "--without_xid" in command
        assert "--fk_mode" in command
        assert "--log_level" in command
        assert "--log_dir" in command
        assert "--no_banner" in command
        assert "--no_progress" in command
        assert "--quiet_ft" in command
        assert "--license" in command

    def test_mask_sensitive_license(self, command_builder):
        """Test that mask_sensitive masks the license value."""
        params = MigrationParams(**_minimal_params(license="SECRET-KEY-123"))
        command = command_builder.build_command(params)
        masked = command_builder.mask_sensitive(command)

        # Original should have the real value
        idx = command.index("--license")
        assert command[idx + 1] == "SECRET-KEY-123"

        # Masked should have ******
        idx = masked.index("--license")
        assert masked[idx + 1] == "******"

    def test_mask_sensitive_preserves_original(self, command_builder):
        """Test that mask_sensitive does not modify the original command."""
        params = MigrationParams(**_minimal_params(license="SECRET-KEY-123"))
        command = command_builder.build_command(params)
        original_command = list(command)
        command_builder.mask_sensitive(command)

        assert command == original_command

    def test_format_command_display_masked(self, command_builder):
        """Test format_command_display with masking (default)."""
        params = MigrationParams(**_minimal_params(license="SECRET-KEY-123"))
        command = command_builder.build_command(params)
        display = command_builder.format_command_display(command, mask=True)

        assert "******" in display
        assert "SECRET-KEY-123" not in display

    def test_format_command_display_unmasked(self, command_builder):
        """Test format_command_display without masking."""
        params = MigrationParams(**_minimal_params(license="SECRET-KEY-123"))
        command = command_builder.build_command(params)
        display = command_builder.format_command_display(command, mask=False)

        assert "SECRET-KEY-123" in display
        assert "******" not in display

    def test_format_command_display_line_continuation(self, command_builder):
        """Test format_command_display uses line continuations."""
        params = MigrationParams(**_minimal_params())
        command = command_builder.build_command(params)
        display = command_builder.format_command_display(command)

        assert " \\\n  " in display

    @patch("subprocess.run")
    def test_execute_command_success(self, mock_run, command_builder):
        """Test successful command execution."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Migration completed successfully"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        command = [str(command_builder.binary_path), "--help"]
        return_code, stdout, stderr = command_builder.execute_command(
            command, timeout=10
        )

        assert return_code == 0
        assert "success" in stdout.lower()
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_execute_command_failure(self, mock_run, command_builder):
        """Test failed command execution."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Connection failed"
        mock_run.return_value = mock_result

        command = [str(command_builder.binary_path), "--help"]
        return_code, stdout, stderr = command_builder.execute_command(
            command, timeout=10
        )

        assert return_code == 1
        assert "failed" in stderr.lower()

    @patch("subprocess.run")
    def test_execute_command_timeout(self, mock_run, command_builder):
        """Test command execution timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=1)

        command = [str(command_builder.binary_path), "--help"]
        with pytest.raises(MigratorXpressError) as exc_info:
            command_builder.execute_command(command, timeout=1)

        assert "timed out" in str(exc_info.value).lower()

    @patch("subprocess.run")
    def test_execute_command_with_logging(self, mock_run, command_builder, tmp_path):
        """Test command execution with log saving."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        log_dir = tmp_path / "logs"
        command = [str(command_builder.binary_path), "--help"]
        command_builder.execute_command(command, timeout=10, log_dir=log_dir)

        assert log_dir.exists()
        log_files = list(log_dir.glob("migratorxpress_*.log"))
        assert len(log_files) == 1

        log_content = log_files[0].read_text()
        assert "MigratorXpress Execution Log" in log_content
        assert "Return Code: 0" in log_content

    def test_get_version_method(self, command_builder):
        """Test get_version returns structured info."""
        info = command_builder.get_version()

        assert "version" in info
        assert "detected" in info
        assert "binary_path" in info
        assert "capabilities" in info
        assert "source_databases" in info["capabilities"]
        assert "target_databases" in info["capabilities"]
        assert "migration_db_types" in info["capabilities"]
        assert "tasks" in info["capabilities"]
        assert "fk_modes" in info["capabilities"]
        assert "migration_db_modes" in info["capabilities"]
        assert "load_modes" in info["capabilities"]
        assert "supports_no_banner" in info["capabilities"]
        assert "supports_fasttransfer" in info["capabilities"]
        assert "supports_license" in info["capabilities"]

    def test_version_detector_property(self, command_builder):
        """Test version_detector property is accessible."""
        assert command_builder.version_detector is not None


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_supported_capabilities(self):
        """Test getting supported capabilities."""
        caps = get_supported_capabilities()

        assert isinstance(caps, dict)
        assert "Source Databases" in caps
        assert "Target Databases" in caps
        assert "Migration Database" in caps
        assert "Tasks" in caps
        assert "Migration DB Modes" in caps
        assert "Load Modes" in caps
        assert "FK Modes" in caps

        assert len(caps["Source Databases"]) == 4
        assert len(caps["Target Databases"]) == 4
        assert len(caps["Migration Database"]) == 1
        assert len(caps["Tasks"]) == 8
        assert len(caps["Migration DB Modes"]) == 3
        assert len(caps["Load Modes"]) == 2
        assert len(caps["FK Modes"]) == 3

    def test_suggest_workflow_with_constraints(self):
        """Test workflow suggestion with constraints."""
        workflow = suggest_workflow("oracle", "postgresql", include_constraints=True)

        assert workflow["source_type"] == "oracle"
        assert workflow["target_type"] == "postgresql"
        assert workflow["include_constraints"] is True

        tasks = [s["task"] for s in workflow["steps"]]
        assert "translate" in tasks
        assert "create" in tasks
        assert "transfer" in tasks
        assert "diff" in tasks
        assert "copy_pk + copy_ak + copy_fk" in tasks
        assert "all" in tasks

    def test_suggest_workflow_without_constraints(self):
        """Test workflow suggestion without constraints."""
        workflow = suggest_workflow(
            "sqlserver", "postgresql", include_constraints=False
        )

        assert workflow["include_constraints"] is False

        tasks = [s["task"] for s in workflow["steps"]]
        assert "translate" in tasks
        assert "create" in tasks
        assert "transfer" in tasks
        assert "diff" in tasks
        assert "copy_pk + copy_ak + copy_fk" not in tasks
        assert "all" in tasks

    def test_suggest_workflow_steps_have_examples(self):
        """Test that workflow steps contain examples."""
        workflow = suggest_workflow("oracle", "sqlserver")

        for step in workflow["steps"]:
            assert "example" in step
            assert "MigratorXpress" in step["example"]
            assert "description" in step
