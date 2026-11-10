from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from keyvault.config_entry import collect_config_evidence
from keyvault.server_runtime import run


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: p19_launcher.py <variant_spec.json>", file=sys.stderr)
        return 2

    spec_path = Path(sys.argv[1]).resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    data_dir = Path(os.environ["KEYVAULT_DATA_DIR"])
    objective = (spec.get("config") or {}).get("objective")

    record = collect_config_evidence("vault-sync" if objective else "local", objective, data_dir)
    if record:
        print("KEYVAULT_CONFIG_EVIDENCE=" + json.dumps(record, ensure_ascii=False), file=sys.stderr)
        return 20

    run(spec_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
