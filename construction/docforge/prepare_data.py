from __future__ import annotations

import argparse
from pathlib import Path

from content_prepare import copy_seed, generate_seed as _generate_seed


def generate_seed(seed_dir: Path, force: bool = False) -> None:
    _generate_seed("docforge", seed_dir, force=force)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare DocForge data.")
    parser.add_argument("--seed-dir", default="docforge/docforge_data_seed")
    parser.add_argument("--copy-to", default="")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    seed_dir = Path(args.seed_dir)
    generate_seed(seed_dir, force=args.force)
    if args.copy_to:
        copy_seed(seed_dir, Path(args.copy_to), force=args.force)
    print(seed_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

