"""JSON serialization helpers."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from ipaddress import IPv4Address, IPv6Address
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .security import redact


def normalize(value: Any) -> Any:
    """Convert common Python/library objects into JSON-safe values."""

    if isinstance(value, BaseModel):
        return normalize(value.model_dump(mode="json"))
    if is_dataclass(value):
        return normalize(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, IPv4Address | IPv6Address | Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): normalize(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set):
        return [normalize(item) for item in value]
    return value


def safe_data(value: Any) -> Any:
    return redact(normalize(value))

