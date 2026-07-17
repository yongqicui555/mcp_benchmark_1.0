"""Input validation helpers for router-facing operations."""

from __future__ import annotations

import ipaddress
import re

from .errors import RouterOperationError

MAC_RE = re.compile(r"^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$")
NVRAM_KEY_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
SAFE_LABEL_RE = re.compile(r"^[A-Za-z0-9_.: -]{0,64}$")


def normalize_mac(mac: str) -> str:
    if not MAC_RE.fullmatch(mac.strip()):
        raise RouterOperationError(
            code="invalid_mac",
            message="MAC address must use the format AA:BB:CC:DD:EE:FF.",
            details={"mac": mac},
        )
    return mac.strip().upper()


def validate_ip(ip: str) -> str:
    try:
        return str(ipaddress.ip_address(ip.strip()))
    except ValueError as exc:
        raise RouterOperationError(
            code="invalid_ip",
            message="Invalid IP address.",
            details={"ip": ip},
        ) from exc


def validate_port(port: int | str, field_name: str = "port") -> str:
    value = int(port)
    if value < 1 or value > 65535:
        raise RouterOperationError(
            code="invalid_port",
            message=f"{field_name} must be between 1 and 65535.",
            details={field_name: port},
        )
    return str(value)


def validate_port_range(value: str | int, field_name: str = "port") -> str:
    text = str(value).strip()
    for part in text.split(","):
        bounds = part.split(":")
        if len(bounds) > 2:
            raise RouterOperationError(
                code="invalid_port_range",
                message=f"{field_name} supports comma separated ports or a:b ranges.",
                details={field_name: value},
            )
        for bound in bounds:
            validate_port(bound, field_name)
    return text


def validate_nvram_key(key: str) -> str:
    if not NVRAM_KEY_RE.fullmatch(key):
        raise RouterOperationError(
            code="invalid_nvram_key",
            message="NVRAM key contains unsupported characters.",
            details={"key": key},
        )
    return key


def validate_label(value: str, field_name: str) -> str:
    text = value.strip()
    if not SAFE_LABEL_RE.fullmatch(text):
        raise RouterOperationError(
            code="invalid_label",
            message=f"{field_name} contains unsupported characters.",
            details={field_name: value},
        )
    return text

