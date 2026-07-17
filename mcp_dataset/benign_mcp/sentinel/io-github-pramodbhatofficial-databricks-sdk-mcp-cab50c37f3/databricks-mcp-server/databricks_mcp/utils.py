"""Shared utilities for Databricks MCP tools."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any, Iterator


def serialize(obj: Any) -> Any:
    """Convert SDK dataclass objects to JSON-serializable dicts.

    Handles nested dataclasses, lists, and enums.
    """
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [serialize(item) for item in obj]
    if is_dataclass(obj) and not isinstance(obj, type):
        return {k: serialize(v) for k, v in asdict(obj).items() if v is not None}
    if hasattr(obj, "value"):  # Enum
        return obj.value
    if hasattr(obj, "__dict__"):
        return {k: serialize(v) for k, v in obj.__dict__.items() if not k.startswith("_") and v is not None}
    return str(obj)


def paginate(iterator: Iterator[Any], max_items: int = 100) -> list[dict[str, Any]]:
    """Collect paginated SDK results into a list of serialized dicts.

    Args:
        iterator: SDK paginated iterator
        max_items: Maximum items to collect (prevents huge responses)

    Returns:
        List of serialized items
    """
    results = []
    for i, item in enumerate(iterator):
        if i >= max_items:
            break
        results.append(serialize(item))
    return results


def truncate_results(items: list[Any], max_items: int = 50) -> dict[str, Any]:
    """Wrap results with truncation info.

    Returns a dict with 'items', 'count', and 'truncated' fields.
    """
    truncated = len(items) > max_items
    return {
        "items": items[:max_items],
        "count": len(items),
        "truncated": truncated,
    }


def format_error(e: Exception) -> str:
    """Format SDK exceptions into consistent error messages."""
    error_type = type(e).__name__
    message = str(e)

    # Extract useful info from Databricks API errors
    if hasattr(e, "error_code"):
        return f"{error_type}: [{e.error_code}] {message}"
    return f"{error_type}: {message}"


def to_json(obj: Any) -> str:
    """Serialize an object to a formatted JSON string."""
    return json.dumps(serialize(obj), indent=2, default=str)
