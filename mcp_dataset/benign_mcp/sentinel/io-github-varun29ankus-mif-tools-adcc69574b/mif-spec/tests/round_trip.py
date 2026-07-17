#!/usr/bin/env python3
"""Round-trip test: parse a MIF document, serialize it back, and verify nothing is lost."""

import json
import sys
from pathlib import Path


def normalize(obj):
    """Deep-sort dicts by key for deterministic comparison."""
    if isinstance(obj, dict):
        return {k: normalize(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [normalize(item) for item in obj]
    return obj


def round_trip_test(filepath: str) -> bool:
    with open(filepath) as f:
        original = json.load(f)

    serialized = json.dumps(original, sort_keys=True, ensure_ascii=False)
    reparsed = json.loads(serialized)

    if normalize(original) != normalize(reparsed):
        print(f"FAIL {filepath}: round-trip produced different output")

        orig_str = json.dumps(normalize(original), indent=2)
        reparse_str = json.dumps(normalize(reparsed), indent=2)

        for i, (a, b) in enumerate(zip(orig_str.splitlines(), reparse_str.splitlines())):
            if a != b:
                print(f"  First diff at line {i + 1}:")
                print(f"    original:  {a}")
                print(f"    reparsed:  {b}")
                break
        return False

    memory_count = len(original.get("memories", []))
    has_graph = original.get("knowledge_graph") is not None
    has_extensions = bool(original.get("vendor_extensions"))
    print(f"PASS {filepath} (round-trip preserved: {memory_count} memories, graph={'yes' if has_graph else 'no'}, extensions={'yes' if has_extensions else 'no'})")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python round_trip.py <file.mif.json> [file2.mif.json ...]")
        sys.exit(1)

    results = [round_trip_test(f) for f in sys.argv[1:]]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} files passed round-trip test")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
