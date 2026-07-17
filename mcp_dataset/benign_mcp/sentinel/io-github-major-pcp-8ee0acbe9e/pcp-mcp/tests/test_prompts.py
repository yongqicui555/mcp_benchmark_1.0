"""Tests for MCP prompts."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock

import pytest

from pcp_mcp.prompts import (
    analyze_cpu_usage,
    check_network_performance,
    diagnose_slow_system,
    find_io_bottleneck,
    investigate_memory_usage,
    register_prompts,
)


@pytest.fixture
def prompts_dict() -> dict[str, Callable[..., Any]]:
    """Return a dictionary of all prompt functions."""
    return {
        "diagnose_slow_system": diagnose_slow_system,
        "investigate_memory_usage": investigate_memory_usage,
        "find_io_bottleneck": find_io_bottleneck,
        "analyze_cpu_usage": analyze_cpu_usage,
        "check_network_performance": check_network_performance,
    }


class TestRegisterPrompts:
    def test_registers_all_prompts(self, prompts_dict) -> None:
        """Test that all prompts are registered."""
        expected_prompts = {
            "diagnose_slow_system",
            "investigate_memory_usage",
            "find_io_bottleneck",
            "analyze_cpu_usage",
            "check_network_performance",
        }
        assert set(prompts_dict.keys()) == expected_prompts

    def test_register_prompts_calls_add_prompt(self) -> None:
        """Test that register_prompts calls mcp.add_prompt for each prompt."""
        mcp = MagicMock()
        register_prompts(mcp)

        # Verify add_prompt was called 5 times (once for each prompt)
        assert mcp.add_prompt.call_count == 5


class TestPromptContent:
    @pytest.mark.parametrize(
        ("prompt_name", "expected_keywords"),
        [
            (
                "diagnose_slow_system",
                ["get_system_snapshot", "get_process_top", "cpu", "memory", "disk"],
            ),
            (
                "investigate_memory_usage",
                ["memory", "swap", "mem.util", "rss_bytes", "get_process_top"],
            ),
            (
                "find_io_bottleneck",
                ["disk", "iowait", "disk.dev", "read", "write", "get_system_snapshot"],
            ),
            (
                "analyze_cpu_usage",
                ["cpu", "user", "system", "idle", "load", "kernel.percpu.cpu"],
            ),
            (
                "check_network_performance",
                ["network", "throughput", "interface", "packets", "errors"],
            ),
        ],
    )
    def test_prompt_contains_expected_keywords(
        self,
        prompts_dict: dict[str, Callable[..., Any]],
        prompt_name: str,
        expected_keywords: list[str],
    ) -> None:
        """Test that prompts contain expected keywords."""
        content = prompts_dict[prompt_name]()

        for keyword in expected_keywords:
            assert keyword.lower() in content.lower(), f"'{keyword}' not found in {prompt_name}"
