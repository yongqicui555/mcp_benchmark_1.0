from __future__ import annotations

from asuswrt_mcp.ssh_parsers import (
    parse_cron_jobs,
    merge_client_sources,
    parse_df_output,
    parse_dnsmasq_leases,
    parse_ip_rules,
    parse_lsmod,
    parse_load_average,
    parse_meminfo,
    parse_mount_output,
    parse_netstat_listeners,
    parse_proc_partitions,
    parse_proc_net_dev,
    parse_route_table,
    parse_uptime_seconds,
)


def test_parse_dnsmasq_leases() -> None:
    raw = "83384 00:1d:c0:66:70:60 192.168.2.6 envoy 01:00:1d:c0:66:70:60"

    leases = parse_dnsmasq_leases(raw)

    assert leases[0].mac == "00:1D:C0:66:70:60"
    assert leases[0].hostname == "envoy"


def test_parse_health_helpers() -> None:
    assert parse_uptime_seconds("48409.39 82525.31") == 48409.39
    assert parse_load_average("19.32 18.83 16.90 1/160 30524")["5m"] == 18.83
    assert parse_meminfo("MemTotal: 255708 kB\nMemFree: 103480 kB") == {
        "MemTotal": 255708,
        "MemFree": 103480,
    }


def test_merge_client_sources() -> None:
    leases_raw = (
        "83384 00:1d:c0:66:70:60 192.168.2.6 envoy 01:00:1d:c0:66:70:60\n"
    )
    clientlist_raw = (
        '{"AP":{"2G":{"00:1D:C0:66:70:60":{"ip":"192.168.2.6","rssi":"-43"}}}}'
    )
    neighbors_raw = "192.168.2.6 dev br0 lladdr 00:1d:c0:66:70:60 REACHABLE\n"

    clients = merge_client_sources(
        leases_raw=leases_raw,
        clientlist_raw=clientlist_raw,
        neighbors_raw=neighbors_raw,
    )

    assert clients[0]["hostname"] == "envoy"
    assert clients[0]["connection"] == "wireless"
    assert clients[0]["band"] == "2G"
    assert clients[0]["rssi"] == -43


def test_parse_storage_and_mount_helpers() -> None:
    df_raw = (
        "Filesystem           1K-blocks      Used Available Use% Mounted on\n"
        "/dev/root                28672     28672         0 100% /\n"
        "tmpfs                   127852      1248    126604   1% /tmp\n"
    )
    mount_raw = (
        "/dev/root on / type squashfs (ro,relatime)\n"
        "tmpfs on /tmp type tmpfs (rw,nosuid,nodev,relatime)\n"
    )

    filesystems = parse_df_output(df_raw)
    mounts = parse_mount_output(mount_raw)

    assert filesystems[0]["blocks_kb"] == 28672
    assert filesystems[1]["mount_point"] == "/tmp"
    assert mounts[0]["filesystem_type"] == "squashfs"
    assert mounts[1]["options"][:2] == ["rw", "nosuid"]


def test_parse_routes_rules_and_partitions() -> None:
    route_raw = (
        "default via 192.168.1.1 dev vlan2\n"
        "192.168.2.0/24 dev br0 proto kernel scope link src 192.168.2.1\n"
    )
    rules_raw = (
        "0: from all lookup local\n"
        "32766: from all lookup main\n"
        "32767: from all lookup default\n"
    )
    partitions_raw = (
        "major minor  #blocks  name\n\n"
        "  31        0      28672 mtdblock0\n"
        "   8        1   15633408 sda1\n"
    )

    routes = parse_route_table(route_raw)
    rules = parse_ip_rules(rules_raw)
    partitions = parse_proc_partitions(partitions_raw)

    assert routes[0]["gateway"] == "192.168.1.1"
    assert routes[1]["source"] == "192.168.2.1"
    assert rules[1]["priority"] == 32766
    assert partitions[1]["name"] == "sda1"


def test_parse_interface_ports_modules_and_cron() -> None:
    netdev_raw = (
        "Inter-|   Receive                                                |  Transmit\n"
        " face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed\n"
        "  br0: 1234567 1000 0 0 0 0 0 0 7654321 900 0 0 0 0 0 0\n"
    )
    netstat_raw = (
        "Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name\n"
        "tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      250/dropbear\n"
        "udp        0      0 0.0.0.0:53              0.0.0.0:*                           232/dnsmasq\n"
    )
    lsmod_raw = (
        "Module                  Size  Used by\n"
        "nf_conntrack           16384  2\n"
        "iptable_filter          2048  1\n"
    )
    cron_raw = "*/5 * * * * service restart_dnsmasq\n0 3 * * * echo rotate-logs\n"

    interfaces = parse_proc_net_dev(netdev_raw)
    listeners = parse_netstat_listeners(netstat_raw)
    modules = parse_lsmod(lsmod_raw)
    jobs = parse_cron_jobs(cron_raw)

    assert interfaces[0]["rx_packets"] == 1000
    assert listeners[0]["state"] == "LISTEN"
    assert listeners[1]["protocol"] == "udp"
    assert modules[0]["used_by_count"] == 2
    assert jobs[0]["command"] == "service restart_dnsmasq"
