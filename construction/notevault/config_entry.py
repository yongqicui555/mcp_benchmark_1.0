from __future__ import annotations

from pathlib import Path

from content_config_entry import collect_config_evidence as _collect_config_evidence
from content_config_entry import main_for_base


def collect_config_evidence(profile: str, objective: str | None, data_dir: Path) -> dict[str, object] | None:
    return _collect_config_evidence("notevault", profile, objective, data_dir)


def main(argv: list[str] | None = None) -> int:
    return main_for_base("notevault", argv)


if __name__ == "__main__":
    raise SystemExit(main())

