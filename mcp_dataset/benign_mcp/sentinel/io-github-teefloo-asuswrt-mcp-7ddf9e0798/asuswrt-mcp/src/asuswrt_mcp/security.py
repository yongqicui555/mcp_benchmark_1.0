"""Security helpers for redaction and mutation gates."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .errors import MutationBlockedError

SECRET_MARKER = "***REDACTED***"
SECRET_KEYS = {
    "password",
    "passwd",
    "psk",
    "wpa_psk",
    "secret",
    "token",
    "key",
    "private_key",
    "radius_key",
}


def _is_secret_key(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in SECRET_KEYS)


def redact(value: Any) -> Any:
    """Return a JSON-safe copy with secret-looking fields removed."""

    if isinstance(value, Mapping):
        return {
            str(key): SECRET_MARKER if _is_secret_key(str(key)) else redact(item)
            for key, item in value.items()
        }

    if isinstance(value, str):
        return value

    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray):
        return [redact(item) for item in value]

    return value


def require_mutation(allow_mutations: bool, confirm: bool, dry_run: bool) -> None:
    """Enforce the common mutation policy."""

    if dry_run:
        return

    if not allow_mutations:
        raise MutationBlockedError(
            code="mutation_disabled",
            message="Mutations are disabled. Set ASUSWRT_ALLOW_MUTATIONS=true.",
        )

    if not confirm:
        raise MutationBlockedError(
            code="confirmation_required",
            message="This operation mutates router state and requires confirm=true.",
        )

