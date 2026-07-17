"""Pytest fixtures and collection hooks for bakom-mcp.

Markiert alle bestehenden Tests in test_integration.py / test_20_*.py /
test_scenarios_20.py automatisch als `live`, weil sie gegen Live-APIs
(geo.admin.ch, opendata.swiss, rtvdb.ofcomnet.ch) laufen.

CI ruft `pytest -m "not live"`, lokal optional `pytest -m live` fuer
Integrationschecks gegen die echten APIs.
"""

from __future__ import annotations

import pytest

# Test-Module, deren Funktionen alle Live-APIs ansprechen.
# Werden in CI standardmaessig uebersprungen (pytest -m "not live").
_LIVE_TEST_MODULES: frozenset[str] = frozenset(
    {
        "tests/test_integration.py",
        "tests/test_20_szenarien.py",
        "tests/test_20_neue_szenarien.py",
        "tests/test_scenarios_20.py",
    }
)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-applies the `live` marker to tests in known live-API modules."""
    rootpath = config.rootpath
    live_marker = pytest.mark.live
    for item in items:
        try:
            relative = item.path.relative_to(rootpath).as_posix()
        except ValueError:
            continue
        if relative in _LIVE_TEST_MODULES:
            item.add_marker(live_marker)
