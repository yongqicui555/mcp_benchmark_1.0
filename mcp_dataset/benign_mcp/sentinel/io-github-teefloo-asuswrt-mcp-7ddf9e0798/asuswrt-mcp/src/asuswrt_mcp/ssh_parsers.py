"""Helpers for SSH-first snapshots on AsusWRT."""

from __future__ import annotations

import json
from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any

from .validators import normalize_mac, validate_ip


@dataclass(frozen=True, slots=True)
class DhcpLease:
    expires_in_seconds: int
    mac: str
    ip: str
    hostname: str = ""
    client_id: str = ""


def parse_uptime_seconds(raw: str) -> float:
    try:
        return float(raw.strip().split()[0])
    except (IndexError, ValueError):
        return 0.0


def parse_load_average(raw: str) -> dict[str, float]:
    parts = raw.strip().split()
    try:
        values = [float(part) for part in parts[:3]]
    except ValueError:
        values = []
    while len(values) < 3:
        values.append(0.0)
    return {"1m": values[0], "5m": values[1], "15m": values[2]}


def parse_meminfo(raw: str) -> dict[str, int]:
    values: dict[str, int] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        token = value.strip().split()[0]
        try:
            values[key] = int(token)
        except ValueError:
            continue
    return values


def parse_dnsmasq_leases(raw: str) -> list[DhcpLease]:
    leases: list[DhcpLease] = []
    for line in raw.splitlines():
        parts = line.split(maxsplit=4)
        if len(parts) < 5:
            continue
        expiry, mac, ip, hostname, client_id = parts
        try:
            expires_in_seconds = int(expiry)
        except ValueError:
            continue
        leases.append(
            DhcpLease(
                expires_in_seconds=expires_in_seconds,
                mac=normalize_mac(mac),
                ip=validate_ip(ip),
                hostname="" if hostname == "*" else hostname,
                client_id="" if client_id == "*" else client_id,
            )
        )
    return leases


def parse_neighbor_table(raw: str) -> dict[str, dict[str, Any]]:
    neighbors: dict[str, dict[str, Any]] = {}
    for line in raw.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        ip = validate_ip(parts[0])
        entry: dict[str, Any] = {"ip": ip, "state": parts[-1]}
        if "lladdr" in parts:
            index = parts.index("lladdr")
            if index + 1 < len(parts):
                entry["mac"] = normalize_mac(parts[index + 1])
        if "dev" in parts:
            index = parts.index("dev")
            if index + 1 < len(parts):
                entry["interface"] = parts[index + 1]
        neighbors[ip] = entry
    return neighbors


def parse_clientlist_json(raw: str) -> dict[str, dict[str, Any]]:
    if not raw.strip():
        return {}

    data = json.loads(raw)
    clients: dict[str, dict[str, Any]] = {}
    for ap_mac, ap_groups in data.items():
        if not isinstance(ap_groups, dict):
            continue
        for group_name, members in ap_groups.items():
            if not isinstance(members, dict):
                continue
            connection = "wired" if group_name == "wired_mac" else "wireless"
            band = None if connection == "wired" else group_name
            for mac, member_data in members.items():
                if not isinstance(member_data, dict):
                    continue
                safe_mac = normalize_mac(mac)
                client = clients.setdefault(safe_mac, {"mac": safe_mac})
                try:
                    client["ap_mac"] = normalize_mac(ap_mac)
                except Exception:  # noqa: BLE001 - allow simplified synthetic inputs
                    client["ap_mac"] = ap_mac
                client["connection"] = connection
                if band:
                    client["band"] = band
                if "ip" in member_data and member_data["ip"]:
                    client["ip"] = validate_ip(str(member_data["ip"]))
                if "rssi" in member_data and str(member_data["rssi"]).strip():
                    try:
                        client["rssi"] = int(member_data["rssi"])
                    except ValueError:
                        pass
    return clients


def merge_client_sources(
    *,
    leases_raw: str,
    clientlist_raw: str,
    neighbors_raw: str,
) -> list[dict[str, Any]]:
    clients: dict[str, dict[str, Any]] = {}

    for lease in parse_dnsmasq_leases(leases_raw):
        clients[lease.mac] = {
            "mac": lease.mac,
            "ip": lease.ip,
            "hostname": lease.hostname,
            "lease_expires_in_seconds": lease.expires_in_seconds,
            "client_id": lease.client_id,
        }

    for mac, data in parse_clientlist_json(clientlist_raw).items():
        clients.setdefault(mac, {"mac": mac}).update(data)

    for neighbor in parse_neighbor_table(neighbors_raw).values():
        mac = neighbor.get("mac")
        if not mac:
            continue
        client = clients.setdefault(mac, {"mac": mac})
        client.setdefault("ip", neighbor["ip"])
        client["neighbor_state"] = neighbor.get("state")
        client["interface"] = neighbor.get("interface")

    def sort_key(item: dict[str, Any]) -> tuple[int, str]:
        ip = item.get("ip")
        if isinstance(ip, str):
            try:
                return (0, ip_address(ip).packed.hex())
            except ValueError:
                pass
        return (1, item["mac"])

    return sorted(clients.values(), key=sort_key)


def parse_process_table(raw: str) -> list[dict[str, Any]]:
    processes: list[dict[str, Any]] = []
    for line in raw.splitlines():
        parts = line.split(maxsplit=4)
        if len(parts) < 5:
            continue
        pid, user, size, state, command = parts
        try:
            process = {
                "pid": int(pid),
                "user": user,
                "size_kb": int(size),
                "state": state,
                "command": command,
                "name": command.split()[0],
            }
        except ValueError:
            continue
        processes.append(process)
    return processes


def parse_df_output(raw: str) -> list[dict[str, Any]]:
    filesystems: list[dict[str, Any]] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith("filesystem"):
            continue
        parts = stripped.split()
        if len(parts) < 6:
            continue
        try:
            filesystems.append(
                {
                    "filesystem": parts[0],
                    "blocks_kb": int(parts[1]),
                    "used_kb": int(parts[2]),
                    "available_kb": int(parts[3]),
                    "use_percent": parts[4],
                    "mount_point": " ".join(parts[5:]),
                }
            )
        except ValueError:
            continue
    return filesystems


def parse_mount_output(raw: str) -> list[dict[str, Any]]:
    mounts: list[dict[str, Any]] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if " on " not in stripped or " type " not in stripped:
            continue
        source, rest = stripped.split(" on ", 1)
        mount_point, rest = rest.split(" type ", 1)
        fs_type, _, options_raw = rest.partition(" (")
        options = options_raw.removesuffix(")").split(",") if options_raw else []
        mounts.append(
            {
                "source": source,
                "mount_point": mount_point,
                "filesystem_type": fs_type,
                "options": [option for option in options if option],
            }
        )
    return mounts


def parse_route_table(raw: str) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    for line in raw.splitlines():
        parts = line.split()
        if not parts:
            continue
        route: dict[str, Any] = {"destination": parts[0], "raw": line.strip()}
        for token, key in (
            ("via", "gateway"),
            ("dev", "interface"),
            ("src", "source"),
            ("proto", "protocol"),
            ("scope", "scope"),
            ("metric", "metric"),
        ):
            if token in parts:
                index = parts.index(token)
                if index + 1 < len(parts):
                    route[key] = parts[index + 1]
        routes.append(route)
    return routes


def parse_ip_rules(raw: str) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or ":" not in stripped:
            continue
        priority, _, rule = stripped.partition(":")
        try:
            rules.append({"priority": int(priority), "rule": rule.strip()})
        except ValueError:
            continue
    return rules


def parse_proc_partitions(raw: str) -> list[dict[str, Any]]:
    partitions: list[dict[str, Any]] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("major") or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) != 4:
            continue
        try:
            partitions.append(
                {
                    "major": int(parts[0]),
                    "minor": int(parts[1]),
                    "blocks_kb": int(parts[2]),
                    "name": parts[3],
                }
            )
        except ValueError:
            continue
    return partitions


def parse_proc_net_dev(raw: str) -> list[dict[str, Any]]:
    interfaces: list[dict[str, Any]] = []
    for line in raw.splitlines():
        if ":" not in line:
            continue
        name, payload = line.split(":", 1)
        interface = name.strip()
        if interface in {"Inter-|", "face"}:
            continue
        values = payload.split()
        if len(values) < 16:
            continue
        try:
            interfaces.append(
                {
                    "interface": interface,
                    "rx_bytes": int(values[0]),
                    "rx_packets": int(values[1]),
                    "rx_errors": int(values[2]),
                    "tx_bytes": int(values[8]),
                    "tx_packets": int(values[9]),
                    "tx_errors": int(values[10]),
                }
            )
        except ValueError:
            continue
    return interfaces


def parse_lsmod(raw: str) -> list[dict[str, Any]]:
    modules: list[dict[str, Any]] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith("module"):
            continue
        parts = stripped.split()
        if len(parts) < 3:
            continue
        try:
            modules.append(
                {
                    "name": parts[0],
                    "size": int(parts[1]),
                    "used_by_count": int(parts[2]),
                    "used_by": parts[3].split(",") if len(parts) > 3 else [],
                }
            )
        except ValueError:
            continue
    return modules


def parse_netstat_listeners(raw: str) -> list[dict[str, Any]]:
    listeners: list[dict[str, Any]] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith("active"):
            continue
        if stripped.startswith("Proto") or stripped.startswith("tcpdump"):
            continue
        parts = stripped.split()
        if len(parts) < 4:
            continue
        proto = parts[0]
        if not proto.startswith(("tcp", "udp")):
            continue
        state = ""
        address_index = 3
        pid_program = ""
        if proto.startswith("tcp"):
            if len(parts) < 6:
                continue
            state = parts[5]
            pid_program = parts[6] if len(parts) > 6 else ""
        else:
            pid_program = parts[5] if len(parts) > 5 else ""
        listeners.append(
            {
                "protocol": proto,
                "local_address": parts[address_index],
                "foreign_address": parts[address_index + 1],
                "state": state,
                "pid_program": pid_program,
            }
        )
    return listeners


def parse_cron_jobs(raw: str) -> list[dict[str, str]]:
    jobs: list[dict[str, str]] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(None, 5)
        if len(parts) < 6:
            jobs.append({"raw": stripped})
            continue
        schedule = " ".join(parts[:5])
        jobs.append({"schedule": schedule, "command": parts[5], "raw": stripped})
    return jobs
