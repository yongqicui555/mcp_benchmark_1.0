"""
MigratorXpress command builder and executor.

This module provides functionality to build, validate, and execute
MigratorXpress commands with proper security measures.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from .validators import MigrationParams
from .version import VersionDetector


logger = logging.getLogger(__name__)


class MigratorXpressError(Exception):
    """Base exception for MigratorXpress operations."""

    pass


class CommandBuilder:
    """Builds MigratorXpress commands from validated parameters."""

    def __init__(self, binary_path: str):
        """
        Initialize the command builder.

        Args:
            binary_path: Path to the MigratorXpress binary
        """
        self.binary_path = Path(binary_path)
        self._preview_only = False
        self._validate_binary()
        self._version_detector = VersionDetector(str(self.binary_path))
        if not self._preview_only:
            detected = self._version_detector.detect()
            if detected:
                logger.info(f"MigratorXpress version {detected} detected")
            else:
                logger.warning("Could not detect MigratorXpress version")
        else:
            # Skip version detection; use latest known capabilities as fallback
            self._version_detector._detection_done = True
            logger.info(
                "Running in command builder mode (binary not configured)"
            )

    @property
    def version_detector(self) -> VersionDetector:
        """Access the version detector instance."""
        return self._version_detector

    def get_version(self) -> Dict[str, Any]:
        """Get version information and capabilities.

        Returns:
            Dict with version string, detection status, binary path, and capabilities.
            When in preview-only mode, includes preview_only flag and install message.
        """
        if self._preview_only:
            caps = self._version_detector.capabilities
            return {
                "preview_only": True,
                "binary_path": str(self.binary_path),
                "message": "Set binary path to enable execution. Download from https://arpe.io",
                "version": None,
                "detected": False,
                "capabilities": {
                    "source_databases": sorted(caps.source_databases),
                    "target_databases": sorted(caps.target_databases),
                    "migration_db_types": sorted(caps.migration_db_types),
                    "tasks": sorted(caps.tasks),
                    "fk_modes": sorted(caps.fk_modes),
                    "migration_db_modes": sorted(caps.migration_db_modes),
                    "load_modes": sorted(caps.load_modes),
                    "supports_no_banner": caps.supports_no_banner,
                    "supports_version_flag": caps.supports_version_flag,
                    "supports_fasttransfer": caps.supports_fasttransfer,
                    "supports_license": caps.supports_license,
                    "supports_no_progress": caps.supports_no_progress,
                    "supports_quiet_ft": caps.supports_quiet_ft,
                    "supports_log_dir": caps.supports_log_dir,
                },
            }

        detected = self._version_detector.detect()
        caps = self._version_detector.capabilities

        return {
            "preview_only": False,
            "version": str(detected) if detected else None,
            "detected": detected is not None,
            "binary_path": str(self.binary_path),
            "capabilities": {
                "source_databases": sorted(caps.source_databases),
                "target_databases": sorted(caps.target_databases),
                "migration_db_types": sorted(caps.migration_db_types),
                "tasks": sorted(caps.tasks),
                "fk_modes": sorted(caps.fk_modes),
                "migration_db_modes": sorted(caps.migration_db_modes),
                "load_modes": sorted(caps.load_modes),
                "supports_no_banner": caps.supports_no_banner,
                "supports_version_flag": caps.supports_version_flag,
                "supports_fasttransfer": caps.supports_fasttransfer,
                "supports_license": caps.supports_license,
                "supports_no_progress": caps.supports_no_progress,
                "supports_quiet_ft": caps.supports_quiet_ft,
                "supports_log_dir": caps.supports_log_dir,
            },
        }

    def _validate_binary(self) -> None:
        """Validate that MigratorXpress binary exists and is executable.

        If the binary is not found, sets preview-only mode instead of raising.
        """
        if not self.binary_path.exists():
            self._preview_only = True
            logger.warning(
                f"MigratorXpress binary not found at: {self.binary_path}. "
                "Set binary path to enable execution. Download from https://arpe.io"
            )
            return

        if not self.binary_path.is_file():
            self._preview_only = True
            logger.warning(
                f"MigratorXpress path is not a file: {self.binary_path}. "
                "Set binary path to enable execution. Download from https://arpe.io"
            )
            return

        if not os.access(self.binary_path, os.X_OK):
            self._preview_only = True
            logger.warning(
                f"MigratorXpress binary is not executable: {self.binary_path}. "
                "Set binary path to enable execution. Download from https://arpe.io"
            )
            return

    def build_command(self, params: MigrationParams) -> List[str]:
        """
        Build a MigratorXpress command from validated parameters.

        MigratorXpress is a single-command CLI — no subcommands.

        Args:
            params: Validated migration parameters

        Returns:
            Command as list of strings (suitable for subprocess)
        """
        cmd = [str(self.binary_path)]

        # Auth file (required)
        cmd.extend(["-a", params.auth_file])

        # Required database identifiers
        cmd.extend(["--source_db_auth_id", params.source_db_auth_id])
        cmd.extend(["--source_db_name", params.source_db_name])
        cmd.extend(["--target_db_auth_id", params.target_db_auth_id])
        cmd.extend(["--target_db_name", params.target_db_name])
        cmd.extend(["--migration_db_auth_id", params.migration_db_auth_id])

        # Schema names
        if params.source_schema_name:
            cmd.extend(["--source_schema_name", params.source_schema_name])
        if params.target_schema_name:
            cmd.extend(["--target_schema_name", params.target_schema_name])

        # Task list (nargs='+')
        if params.task_list:
            cmd.append("--task_list")
            cmd.extend(params.task_list)

        # Resume
        if params.resume:
            cmd.extend(["-r", params.resume])

        # FastTransfer
        if params.fasttransfer_dir_path:
            cmd.extend(["--fasttransfer_dir_path", params.fasttransfer_dir_path])
        if params.fasttransfer_p is not None:
            cmd.extend(["-p", str(params.fasttransfer_p)])
        if params.ft_large_table_th is not None:
            cmd.extend(["--ft_large_table_th", str(params.ft_large_table_th)])

        # Parallelism
        if params.n_jobs is not None:
            cmd.extend(["--n_jobs", str(params.n_jobs)])

        # Index thresholds
        if params.cci_threshold is not None:
            cmd.extend(["--cci_threshold", str(params.cci_threshold)])
        if params.aci_threshold is not None:
            cmd.extend(["--aci_threshold", str(params.aci_threshold)])

        # Migration DB mode
        if params.migration_db_mode:
            cmd.extend(["--migration_db_mode", params.migration_db_mode.value])

        # String-boolean parameters
        if params.compute_nbrows is not None:
            cmd.extend(["--compute_nbrows", params.compute_nbrows])
        if params.drop_tables_if_exists is not None:
            cmd.extend(["--drop_tables_if_exists", params.drop_tables_if_exists])

        # Load mode
        if params.load_mode:
            cmd.extend(["--load_mode", params.load_mode.value])

        # Filtering
        if params.include_tables:
            cmd.extend(["-i", params.include_tables])
        if params.exclude_tables:
            cmd.extend(["-e", params.exclude_tables])
        if params.min_rows is not None:
            cmd.extend(["-min", str(params.min_rows)])
        if params.max_rows is not None:
            cmd.extend(["-max", str(params.max_rows)])

        # Oracle-specific lists (nargs='+')
        if params.forced_int_id_prefixes:
            cmd.append("--forced_int_id_prefixes")
            cmd.extend(params.forced_int_id_prefixes)
        if params.forced_int_id_suffixes:
            cmd.append("--forced_int_id_suffixes")
            cmd.extend(params.forced_int_id_suffixes)

        # Profiling
        if params.profiling_sample_pc is not None:
            cmd.extend(["--profiling_sample_pc", str(params.profiling_sample_pc)])
        if params.p_query is not None:
            cmd.extend(["--p_query", str(params.p_query)])
        if params.min_sample_pc_profile is not None:
            cmd.extend(["--min_sample_pc_profile", str(params.min_sample_pc_profile)])

        # Boolean flags
        if params.force:
            cmd.append("-f")
        if params.basic_diff:
            cmd.append("--basic_diff")
        if params.without_xid:
            cmd.append("--without_xid")

        # FK mode
        if params.fk_mode:
            cmd.extend(["--fk_mode", params.fk_mode.value])

        # Logging
        if params.log_level:
            cmd.extend(["--log_level", params.log_level.value])
        if params.log_dir:
            cmd.extend(["--log_dir", params.log_dir])

        # Display flags
        if params.no_banner:
            cmd.append("--no_banner")
        if params.no_progress:
            cmd.append("--no_progress")
        if params.quiet_ft:
            cmd.append("--quiet_ft")

        # License
        if params.license:
            cmd.extend(["--license", params.license])
        if params.license_file:
            cmd.extend(["--license_file", params.license_file])

        return cmd

    def mask_sensitive(self, command: List[str]) -> List[str]:
        """
        Return a copy of the command with sensitive values masked.

        Masks the value following --license with '******'.

        Args:
            command: Original command list

        Returns:
            New list with sensitive values masked
        """
        masked = list(command)
        for i, token in enumerate(masked):
            if token == "--license" and i + 1 < len(masked):
                masked[i + 1] = "******"
        return masked

    def format_command_display(self, command: List[str], mask: bool = True, os_type: str = "linux") -> str:
        """
        Format command for display.

        Args:
            command: Command list
            mask: Whether to mask sensitive values (default True)
            os_type: Target operating system for command formatting ("linux" or "windows")

        Returns:
            Formatted command string
        """
        display_cmd = self.mask_sensitive(command) if mask else command

        # Adjust binary path for Windows
        if os_type == "windows":
            binary = display_cmd[0].replace("/", "\\")
            if not binary.endswith(".exe"):
                binary += ".exe"
            formatted_parts = [binary]
        else:
            formatted_parts = [display_cmd[0]]

        i = 1
        while i < len(display_cmd):
            if i < len(display_cmd) - 1 and display_cmd[i].startswith("-") and not display_cmd[i + 1].startswith("-"):
                param = display_cmd[i]
                value = display_cmd[i + 1]
                if " " in value:
                    formatted_parts.append(f'{param} "{value}"')
                else:
                    formatted_parts.append(f"{param} {value}")
                i += 2
            else:
                formatted_parts.append(display_cmd[i])
                i += 1

        if os_type == "windows":
            return " ^\n  ".join(formatted_parts)
        return " \\\n  ".join(formatted_parts)

    def execute_command(
        self, command: List[str], timeout: int = 3600, log_dir: Optional[Path] = None
    ) -> Tuple[int, str, str]:
        """
        Execute a MigratorXpress command.

        Args:
            command: Command to execute
            timeout: Timeout in seconds (default: 3600 = 1 hour)
            log_dir: Directory for execution logs

        Returns:
            Tuple of (return_code, stdout, stderr)

        Raises:
            MigratorXpressError: If in preview-only mode or execution fails/times out
        """
        if self._preview_only:
            raise MigratorXpressError(
                "Execution requires the binary. Download from https://arpe.io and configure the binary path."
            )

        start_time = datetime.now()

        logger.info(
            f"Executing MigratorXpress command: {' '.join(self.mask_sensitive(command))}"
        )

        try:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=timeout, check=False
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.info(
                f"MigratorXpress completed in {duration:.2f}s with return code {result.returncode}"
            )

            # Save logs if directory provided
            if log_dir:
                self._save_execution_log(
                    log_dir,
                    command,
                    result.returncode,
                    result.stdout,
                    result.stderr,
                    duration,
                )

            return result.returncode, result.stdout, result.stderr

        except subprocess.TimeoutExpired as e:
            logger.error(f"MigratorXpress execution timed out after {timeout}s")
            raise MigratorXpressError(
                f"Execution timed out after {timeout} seconds"
            ) from e

        except Exception as e:
            logger.error(f"MigratorXpress execution failed: {e}")
            raise MigratorXpressError(f"Execution failed: {e}") from e

    def _save_execution_log(
        self,
        log_dir: Path,
        command: List[str],
        return_code: int,
        stdout: str,
        stderr: str,
        duration: float,
    ) -> None:
        """Save execution log to file."""
        try:
            log_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"migratorxpress_{timestamp}.log"

            with open(log_file, "w") as f:
                f.write("MigratorXpress Execution Log\n")
                f.write(f"{'=' * 80}\n\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Duration: {duration:.2f} seconds\n")
                f.write(f"Return Code: {return_code}\n\n")
                f.write(f"Command:\n{' '.join(self.mask_sensitive(command))}\n\n")
                f.write(f"{'=' * 80}\n")
                f.write(f"STDOUT:\n{stdout}\n\n")
                f.write(f"{'=' * 80}\n")
                f.write(f"STDERR:\n{stderr}\n")

            logger.info(f"Execution log saved to: {log_file}")

        except Exception as e:
            logger.warning(f"Failed to save execution log: {e}")


def get_supported_capabilities() -> Dict[str, Any]:
    """
    Get supported source databases, target databases, migration database types,
    tasks, modes, and other capabilities.

    Returns:
        Dictionary with all supported capabilities
    """
    return {
        "Source Databases": [
            "Oracle (oracle)",
            "PostgreSQL (postgresql)",
            "SQL Server (sqlserver)",
            "Netezza (netezza)",
        ],
        "Target Databases": [
            "PostgreSQL (postgresql)",
            "SQL Server (sqlserver)",
            "MySQL (mysql) — limited: schema creation only",
            "Oracle (oracle)",
        ],
        "Migration Database": [
            "SQL Server (sqlserver)",
        ],
        "Tasks": {
            "translate": "Translate source schema to target schema DDL",
            "create": "Create target tables from translated DDL",
            "transfer": "Transfer data from source to target",
            "diff": "Compare source and target row counts",
            "copy_pk": "Copy primary key constraints to target",
            "copy_ak": "Copy alternate key (unique) constraints to target",
            "copy_fk": "Copy foreign key constraints to target",
            "all": "Run all tasks in sequence (translate, create, transfer, diff, copy_pk, copy_ak, copy_fk)",
        },
        "Migration DB Modes": {
            "preserve": "Keep existing migration database data",
            "truncate": "Clear migration database before run",
            "drop": "Drop and recreate migration database",
        },
        "Load Modes": {
            "truncate": "Truncate target tables before loading",
            "append": "Append data to existing target tables",
        },
        "FK Modes": {
            "trusted": "Create foreign keys as trusted constraints",
            "untrusted": "Create foreign keys as untrusted constraints",
            "disabled": "Create foreign keys in disabled state",
        },
    }


def suggest_workflow(
    source_type: str,
    target_type: str,
    include_constraints: bool = True,
) -> Dict[str, Any]:
    """
    Suggest an ordered workflow of MigratorXpress tasks based on use case.

    Args:
        source_type: Source database type (e.g., 'oracle', 'postgresql')
        target_type: Target database type (e.g., 'postgresql', 'sqlserver')
        include_constraints: Whether to include constraint copy steps

    Returns:
        Dictionary with ordered workflow steps and example parameters
    """
    steps = []

    # Step 1: Translate
    steps.append(
        {
            "step": 1,
            "task": "translate",
            "description": "Translate source schema DDL to target-compatible DDL",
            "example": (
                "MigratorXpress -a auth.json "
                "--source_db_auth_id source_db --source_db_name mydb "
                "--target_db_auth_id target_db --target_db_name targetdb "
                "--migration_db_auth_id migration_db "
                "--task_list translate"
            ),
        }
    )

    # Step 2: Create
    steps.append(
        {
            "step": 2,
            "task": "create",
            "description": "Create target tables from translated DDL",
            "example": (
                "MigratorXpress -a auth.json "
                "--source_db_auth_id source_db --source_db_name mydb "
                "--target_db_auth_id target_db --target_db_name targetdb "
                "--migration_db_auth_id migration_db "
                "--task_list create"
            ),
        }
    )

    # Step 3: Transfer
    steps.append(
        {
            "step": 3,
            "task": "transfer",
            "description": "Transfer data from source to target tables",
            "example": (
                "MigratorXpress -a auth.json "
                "--source_db_auth_id source_db --source_db_name mydb "
                "--target_db_auth_id target_db --target_db_name targetdb "
                "--migration_db_auth_id migration_db "
                "--task_list transfer"
            ),
        }
    )

    # Step 4: Diff
    steps.append(
        {
            "step": 4,
            "task": "diff",
            "description": "Compare source and target row counts to verify transfer",
            "example": (
                "MigratorXpress -a auth.json "
                "--source_db_auth_id source_db --source_db_name mydb "
                "--target_db_auth_id target_db --target_db_name targetdb "
                "--migration_db_auth_id migration_db "
                "--task_list diff"
            ),
        }
    )

    # Step 5: Constraints (optional)
    if include_constraints:
        steps.append(
            {
                "step": 5,
                "task": "copy_pk + copy_ak + copy_fk",
                "description": "Copy primary keys, alternate keys, and foreign keys to target",
                "example": (
                    "MigratorXpress -a auth.json "
                    "--source_db_auth_id source_db --source_db_name mydb "
                    "--target_db_auth_id target_db --target_db_name targetdb "
                    "--migration_db_auth_id migration_db "
                    "--task_list copy_pk copy_ak copy_fk"
                ),
            }
        )

    # Alternative: all
    steps.append(
        {
            "step": "alt",
            "task": "all",
            "description": "Alternative: run all tasks in a single invocation",
            "example": (
                "MigratorXpress -a auth.json "
                "--source_db_auth_id source_db --source_db_name mydb "
                "--target_db_auth_id target_db --target_db_name targetdb "
                "--migration_db_auth_id migration_db "
                "--task_list all"
            ),
        }
    )

    return {
        "source_type": source_type,
        "target_type": target_type,
        "include_constraints": include_constraints,
        "steps": steps,
    }
