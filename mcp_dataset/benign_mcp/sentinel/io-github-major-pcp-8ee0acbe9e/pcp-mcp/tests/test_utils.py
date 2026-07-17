"""Tests for utility functions: builders and extractors."""

from __future__ import annotations

import pytest

from pcp_mcp.utils.builders import (
    assess_processes,
    build_cpu_metrics,
    build_disk_metrics,
    build_load_metrics,
    build_memory_metrics,
    build_network_metrics,
    build_process_list,
    get_sort_key,
)
from pcp_mcp.utils.extractors import (
    extract_help_text,
    extract_timestamp,
    format_units,
    get_first_value,
    get_scalar_value,
    sum_instances,
)


class TestGetFirstValue:
    @pytest.mark.parametrize(
        ("data", "metric", "default", "expected"),
        [
            ({"foo": {"instances": {-1: 42.5}}}, "foo", 0.0, 42.5),
            ({"foo": {"instances": {"cpu0": 10, "cpu1": 20}}}, "foo", 0.0, 10),
            ({}, "missing", 99.0, 99.0),
            ({"foo": {"instances": {}}}, "foo", 5.0, 5.0),
            ({"foo": {}}, "foo", 7.0, 7.0),
        ],
    )
    def test_extraction(self, data: dict, metric: str, default: float, expected: float) -> None:
        assert get_first_value(data, metric, default) == expected


class TestGetScalarValue:
    @pytest.mark.parametrize(
        ("response", "metric", "default", "expected"),
        [
            (
                {"values": [{"name": "hinv.ncpu", "instances": [{"value": 8}]}]},
                "hinv.ncpu",
                0,
                8,
            ),
            (
                {"values": [{"name": "other", "instances": [{"value": 5}]}]},
                "hinv.ncpu",
                99,
                99,
            ),
            ({"values": []}, "missing", 42, 42),
            (
                {"values": [{"name": "empty", "instances": []}]},
                "empty",
                100,
                100,
            ),
        ],
    )
    def test_extraction(self, response: dict, metric: str, default: int, expected: int) -> None:
        assert get_scalar_value(response, metric, default) == expected


class TestSumInstances:
    @pytest.mark.parametrize(
        ("data", "metric", "expected"),
        [
            ({"net.bytes": {"instances": {"eth0": 100, "lo": 50}}}, "net.bytes", 150.0),
            ({"net.bytes": {"instances": {}}}, "net.bytes", 0.0),
            ({}, "missing", 0.0),
        ],
    )
    def test_sum(self, data: dict, metric: str, expected: float) -> None:
        assert sum_instances(data, metric) == expected


class TestExtractHelpText:
    @pytest.mark.parametrize(
        ("metric_dict", "default", "expected"),
        [
            ({"text-help": "Full help"}, "", "Full help"),
            ({"text-oneline": "One liner"}, "", "One liner"),
            ({"text-help": "Full", "text-oneline": "Short"}, "", "Full"),
            ({}, "fallback", "fallback"),
            ({"text-help": "", "text-oneline": "Short"}, "", "Short"),
        ],
    )
    def test_extraction(self, metric_dict: dict, default: str, expected: str) -> None:
        assert extract_help_text(metric_dict, default) == expected


class TestExtractTimestamp:
    @pytest.mark.parametrize(
        ("response", "expected"),
        [
            ({"timestamp": {"s": 1000, "us": 500000}}, 1000.5),
            ({"timestamp": {"s": 1000, "us": 0}}, 1000.0),
            ({"timestamp": 1234.567}, 1234.567),
            ({}, 0.0),
            ({"timestamp": {}}, 0.0),
        ],
    )
    def test_extraction(self, response: dict, expected: float) -> None:
        assert extract_timestamp(response) == pytest.approx(expected)


class TestFormatUnits:
    @pytest.mark.parametrize(
        ("info", "expected"),
        [
            ({"units": "millisec"}, "millisec"),
            ({"units": "byte"}, "byte"),
            ({}, "none"),
            ({"units": ""}, "none"),
            ({"units": "", "units-space": "Kbyte"}, "Kbyte"),
            ({"units": "", "units-time": "sec"}, "sec"),
            ({"units": "", "units-count": "count"}, "count"),
            ({"units": "", "units-space": "Kbyte", "units-time": "sec"}, "Kbyte / sec"),
            (
                {"units": "", "units-space": "Mbyte", "units-time": "sec", "units-count": "count"},
                "Mbyte / sec / count",
            ),
        ],
    )
    def test_format_units(self, info: dict, expected: str) -> None:
        assert format_units(info) == expected


class TestBuildCPUMetrics:
    @pytest.mark.parametrize(
        ("user", "sys", "idle", "iowait", "ncpu", "expected_assessment"),
        [
            (20.0, 10.0, 65.0, 5.0, 4, "normal"),
            (10.0, 5.0, 55.0, 30.0, 4, "I/O wait"),
            (70.0, 20.0, 5.0, 5.0, 4, "saturated"),
            (75.0, 10.0, 10.0, 5.0, 4, "user"),
            (20.0, 35.0, 40.0, 5.0, 4, "system"),
        ],
    )
    def test_assessments(
        self, cpu_metrics_data, user, sys, idle, iowait, ncpu, expected_assessment
    ) -> None:
        data = cpu_metrics_data(user=user, sys=sys, idle=idle, iowait=iowait, ncpu=ncpu)
        result = build_cpu_metrics(data)
        assert expected_assessment.lower() in result.assessment.lower()

    def test_zero_total_cpu(self, cpu_metrics_data) -> None:
        data = cpu_metrics_data(user=0.0, sys=0.0, idle=0.0, iowait=0.0)
        result = build_cpu_metrics(data)
        assert result.user_percent == 0.0
        assert result.idle_percent == 0.0


class TestBuildMemoryMetrics:
    @pytest.mark.parametrize(
        ("physmem", "available", "swap_total", "swap_free", "expected_assessment"),
        [
            (16_000_000, 12_000_000, 8_000_000, 7_000_000, "normal"),
            (16_000_000, 1_000_000, 8_000_000, 7_000_000, "critical"),
            (16_000_000, 3_000_000, 8_000_000, 7_000_000, "elevated"),
            (16_000_000, 10_000_000, 8_000_000, 2_000_000, "swap"),
        ],
    )
    def test_assessments(
        self, memory_metrics_data, physmem, available, swap_total, swap_free, expected_assessment
    ) -> None:
        data = memory_metrics_data(
            physmem=physmem, available=available, swap_total=swap_total, swap_free=swap_free
        )
        result = build_memory_metrics(data)
        assert expected_assessment.lower() in result.assessment.lower()


class TestBuildLoadMetrics:
    @pytest.mark.parametrize(
        ("load_1m", "ncpu", "expected_assessment"),
        [
            (2.0, 4, "normal"),
            (6.0, 4, "elevated"),
            (10.0, 4, "high"),
        ],
    )
    def test_assessments(self, load_metrics_data, load_1m, ncpu, expected_assessment) -> None:
        data = load_metrics_data(load_1m=load_1m, ncpu=ncpu)
        result = build_load_metrics(data)
        assert expected_assessment.lower() in result.assessment.lower()


class TestBuildDiskMetrics:
    @pytest.mark.parametrize(
        ("read_bytes", "write_bytes", "expected_assessment"),
        [
            (1_000_000.0, 500_000.0, "low"),
            (15_000_000.0, 5_000_000.0, "moderate"),
            (150_000_000.0, 50_000_000.0, "heavy"),
        ],
    )
    def test_assessments(
        self, disk_metrics_data, read_bytes, write_bytes, expected_assessment
    ) -> None:
        data = disk_metrics_data(read_bytes=read_bytes, write_bytes=write_bytes)
        result = build_disk_metrics(data)
        assert expected_assessment.lower() in result.assessment.lower()


class TestBuildNetworkMetrics:
    @pytest.mark.parametrize(
        ("in_bytes", "out_bytes", "expected_assessment"),
        [
            ({"eth0": 1_000_000.0}, {"eth0": 500_000.0}, "low"),
            ({"eth0": 10_000_000.0}, {"eth0": 5_000_000.0}, "moderate"),
            ({"eth0": 100_000_000.0}, {"eth0": 50_000_000.0}, "high"),
        ],
    )
    def test_assessments(
        self, network_metrics_data, in_bytes, out_bytes, expected_assessment
    ) -> None:
        data = network_metrics_data(in_bytes=in_bytes, out_bytes=out_bytes)
        result = build_network_metrics(data)
        assert expected_assessment.lower() in result.assessment.lower()


class TestBuildProcessList:
    def test_builds_process_list(self, process_metrics_data) -> None:
        data = process_metrics_data()
        processes = build_process_list(data, sort_by="cpu", total_mem=16_000_000_000, ncpu=4)
        assert len(processes) == 2
        assert processes[0].pid == 1234
        assert processes[0].command == "python"

    def test_skips_invalid_pids(self, process_metrics_data) -> None:
        data = process_metrics_data(
            processes=[
                {"inst": 1, "pid": 0, "cmd": "invalid", "args": "", "rss": 0},
                {"inst": 2, "pid": 1234, "cmd": "valid", "args": "valid cmd", "rss": 1000},
            ]
        )
        processes = build_process_list(data, sort_by="cpu", total_mem=16_000_000_000, ncpu=4)
        assert len(processes) == 1
        assert processes[0].pid == 1234

    def test_memory_sort_omits_cpu_and_io_when_data_missing(self) -> None:
        data = {
            "proc.psinfo.pid": {"instances": {1: 1234}},
            "proc.psinfo.cmd": {"instances": {1: "app"}},
            "proc.psinfo.psargs": {"instances": {1: "app --run"}},
            "proc.memory.rss": {"instances": {1: 100_000}},
            "proc.psinfo.utime": {"instances": {}},
            "proc.psinfo.stime": {"instances": {}},
            "proc.io.read_bytes": {"instances": {}},
            "proc.io.write_bytes": {"instances": {}},
        }
        processes = build_process_list(data, sort_by="memory", total_mem=16_000_000_000, ncpu=4)

        assert len(processes) == 1
        assert processes[0].pid == 1234
        assert processes[0].cpu_percent is None
        assert processes[0].io_read_bytes_per_sec is None
        assert processes[0].io_write_bytes_per_sec is None


class TestGetSortKey:
    def test_cpu_sort(self, process_metrics_data) -> None:
        data = process_metrics_data()
        processes = build_process_list(data, sort_by="cpu", total_mem=16_000_000_000, ncpu=4)
        key = get_sort_key(processes[0], "cpu")
        assert key == processes[0].cpu_percent

    def test_memory_sort(self, process_metrics_data) -> None:
        data = process_metrics_data()
        processes = build_process_list(data, sort_by="memory", total_mem=16_000_000_000, ncpu=4)
        key = get_sort_key(processes[0], "memory")
        assert key == float(processes[0].rss_bytes)

    def test_io_sort(self, process_metrics_data) -> None:
        data = process_metrics_data()
        processes = build_process_list(data, sort_by="io", total_mem=16_000_000_000, ncpu=4)
        key = get_sort_key(processes[0], "io")
        expected = (processes[0].io_read_bytes_per_sec or 0) + (
            processes[0].io_write_bytes_per_sec or 0
        )
        assert key == expected

    def test_unknown_sort(self, process_metrics_data) -> None:
        data = process_metrics_data()
        processes = build_process_list(data, sort_by="cpu", total_mem=16_000_000_000, ncpu=4)
        key = get_sort_key(processes[0], "unknown")
        assert key == 0.0


class TestAssessProcesses:
    def test_empty_processes(self) -> None:
        assert assess_processes([], "cpu", 4) == "No processes found"

    def test_cpu_bound_process(self, process_metrics_data) -> None:
        data = process_metrics_data(
            processes=[
                {"inst": 1, "pid": 1, "cmd": "hog", "args": "", "rss": 1000, "utime": 3000.0}
            ]
        )
        procs = build_process_list(data, sort_by="cpu", total_mem=16_000_000_000, ncpu=4)
        assessment = assess_processes(procs, "cpu", 4)
        assert "hog" in assessment

    def test_memory_assessment(self, process_metrics_data) -> None:
        data = process_metrics_data()
        procs = build_process_list(data, sort_by="memory", total_mem=16_000_000_000, ncpu=4)
        procs = sorted(procs, key=lambda p: p.rss_bytes, reverse=True)
        assessment = assess_processes(procs, "memory", 4)
        assert "memory" in assessment.lower()

    def test_io_assessment(self, process_metrics_data) -> None:
        data = process_metrics_data()
        procs = build_process_list(data, sort_by="io", total_mem=16_000_000_000, ncpu=4)
        assessment = assess_processes(procs, "io", 4)
        assert "I/O" in assessment

    def test_unknown_sort_assessment(self, process_metrics_data) -> None:
        data = process_metrics_data()
        procs = build_process_list(data, sort_by="cpu", total_mem=16_000_000_000, ncpu=4)
        assessment = assess_processes(procs, "unknown", 4)
        assert "Top process" in assessment
