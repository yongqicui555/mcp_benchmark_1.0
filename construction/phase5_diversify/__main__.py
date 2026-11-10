"""Phase 5 entry point: python -m phase5_diversify"""
from __future__ import annotations

import sys
from pathlib import Path

from .config import BASE_CONFIGS, BASE_VARIANT_MAPS, REAL_MCP_ROOT
from .transform import diversify_base
from .verify import verify_diversity, verify_cross_diversity


def main():
    print("Phase 5: RSC Payload Technical Diversity")
    print(f"  real_mcp: {REAL_MCP_ROOT}")
    print()

    all_ok = True

    for base_name in BASE_CONFIGS:
        if base_name not in BASE_VARIANT_MAPS:
            print(f"  SKIP: no variant map for {base_name}")
            continue

        real_base = REAL_MCP_ROOT / base_name
        if not real_base.is_dir():
            print(f"  SKIP: {real_base} not found")
            continue

        print(f"\n{'='*60}")
        print(f"Diversifying base: {base_name}")
        print(f"{'='*60}")

        stats = diversify_base(real_base, base_name)
        print(f"  server.py modified: {stats['server_py_modified']}")
        print(f"  mcp_config.json modified: {stats['mcp_config_modified']}")
        print(f"  skipped (V1 unchanged): {stats['skipped_v1']}")
        print(f"  errors: {stats['errors']}")
        print()

        ok = verify_diversity(real_base, base_name)
        if not ok:
            all_ok = False

    # Cross-base diversity verification
    print(f"\n{'='*60}")
    print("Cross-base diversity verification")
    print(f"{'='*60}")
    cross_ok = verify_cross_diversity(REAL_MCP_ROOT)
    if not cross_ok:
        all_ok = False

    if all_ok:
        print(f"\n{'='*60}")
        print("SUCCESS: All bases diversified and verified!")
        print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print("FAILED: Some bases had verification errors")
        print(f"{'='*60}")
        sys.exit(1)


if __name__ == "__main__":
    main()
