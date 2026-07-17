#!/usr/bin/env python3
"""Validate MIF documents against the MIF v2.0 JSON Schema."""

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("Install jsonschema: pip install jsonschema")
    sys.exit(1)


SCHEMA_PATH = Path(__file__).parent / "schema" / "mif-v2.schema.json"


def validate_file(filepath: str) -> bool:
    schema_path = SCHEMA_PATH
    if not schema_path.exists():
        print(f"Schema not found: {schema_path}")
        return False

    with open(schema_path) as f:
        schema = json.load(f)

    with open(filepath) as f:
        try:
            document = json.load(f)
        except json.JSONDecodeError as e:
            print(f"FAIL {filepath}: Invalid JSON — {e}")
            return False

    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(document))

    if not errors:
        memory_count = len(document.get("memories", []))
        has_graph = document.get("knowledge_graph") is not None
        has_extensions = bool(document.get("vendor_extensions"))
        print(f"PASS {filepath}")
        print(f"     {memory_count} memories, graph={'yes' if has_graph else 'no'}, extensions={'yes' if has_extensions else 'no'}")
        return True

    print(f"FAIL {filepath}: {len(errors)} validation error(s)")
    for err in errors[:5]:
        path = " -> ".join(str(p) for p in err.absolute_path) or "(root)"
        print(f"     [{path}] {err.message}")
    if len(errors) > 5:
        print(f"     ... and {len(errors) - 5} more")
    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate.py <file.mif.json> [file2.mif.json ...]")
        print("       python validate.py examples/*.mif.json")
        sys.exit(1)

    files = sys.argv[1:]
    results = []
    for f in files:
        results.append(validate_file(f))

    passed = sum(results)
    total = len(results)
    print(f"\n{passed}/{total} files passed validation")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
