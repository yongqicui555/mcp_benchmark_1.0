"""Phase 3 Converter CLI entry point."""
from __future__ import annotations

import sys
from pathlib import Path

from .converter import convert_all, structural_verification
from .config import BASE_CONFIGS


def main():
    """Run the Phase 3 conversion for all bases."""
    project_root = Path(__file__).resolve().parent.parent
    clean_mcp_dir = project_root / "clean_mcp"
    real_mcp_dir = project_root / "real_mcp"
    
    all_ok = True
    
    for base_name in BASE_CONFIGS:
        print(f"\n{'='*60}")
        print(f"Converting base: {base_name}")
        print(f"{'='*60}")
        
        # Remove existing real_mcp for this base
        base_output = real_mcp_dir / base_name
        if base_output.exists():
            import shutil
            shutil.rmtree(base_output)
        
        # Run conversion
        results = convert_all(clean_mcp_dir, real_mcp_dir, base_name)
        
        # Check results
        fail_count = sum(1 for r in results if not r.ok)
        if fail_count > 0:
            print(f"  {fail_count} variants FAILED for {base_name}")
            all_ok = False
            continue
        
        # Run structural verification
        struct_errors = structural_verification(real_mcp_dir, base_name)
        if struct_errors:
            print(f"  Structural verification FAILED for {base_name}:")
            for err in struct_errors:
                print(f"    {err}")
            all_ok = False
        else:
            print(f"  Structural verification PASSED for {base_name}")
    
    if all_ok:
        print(f"\n{'='*60}")
        print("All bases converted successfully!")
        print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print("Some bases had errors!")
        print(f"{'='*60}")
        sys.exit(1)


if __name__ == "__main__":
    main()
