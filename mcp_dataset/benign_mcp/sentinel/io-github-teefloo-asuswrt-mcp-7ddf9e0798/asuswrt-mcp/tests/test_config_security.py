from __future__ import annotations

from asuswrt_mcp.config import Settings
from asuswrt_mcp.errors import MutationBlockedError
from asuswrt_mcp.security import SECRET_MARKER, redact, require_mutation


def test_settings_redacts_secrets() -> None:
    settings = Settings(
        host="192.168.1.1",
        username="admin",
        password="super-secret",
        ssh_key_file="C:/Users/me/.ssh/id_rsa",
    )

    safe = settings.safe_dict()

    assert safe["password"] == SECRET_MARKER
    assert safe["host"] == "192.168.1.1"


def test_redact_nested_secret_keys() -> None:
    value = {"wifi": {"wpa_psk": "secret"}, "items": [{"token": "abc"}]}

    assert redact(value) == {
        "wifi": {"wpa_psk": SECRET_MARKER},
        "items": [{"token": SECRET_MARKER}],
    }


def test_mutation_requires_allow_flag_and_confirmation() -> None:
    try:
        require_mutation(False, True, False)
    except MutationBlockedError as exc:
        assert exc.code == "mutation_disabled"
    else:
        raise AssertionError("mutation should be blocked")

    try:
        require_mutation(True, False, False)
    except MutationBlockedError as exc:
        assert exc.code == "confirmation_required"
    else:
        raise AssertionError("confirmation should be required")

    require_mutation(False, False, True)
    require_mutation(True, True, False)

