"""Generate five L0 intermediate samples with synthetic data; execute no servers."""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import sys

CONSTRUCTION = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CONSTRUCTION))

from keyvault.prepare_data import generate_seed as keyvault_seed
from devspace.prepare_data import generate_seed as devspace_seed
from content_prepare import generate_seed as content_seed
from scripts import generate_keyvault, generate_devspace
from scripts.content_construct import all_specs, write_clean_variant


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    frozen = CONSTRUCTION.parent / "benchmark"
    if output.is_relative_to(frozen) or frozen.is_relative_to(output):
        parser.error("Output must be separate from the published benchmark")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        parser.error("Output must be a new or empty directory")
    output.mkdir(parents=True, exist_ok=True)
    samples = []
    for base in ("keyvault", "devspace", "notevault", "docforge", "scaffoldkit"):
        seed = output / "seeds" / base
        target = output / "samples" / base
        if base in ("keyvault", "devspace"):
            builder = generate_keyvault if base == "keyvault" else generate_devspace
            (keyvault_seed if base == "keyvault" else devspace_seed)(seed)
            spec = next(s for s in builder.all_specs(builder.load_meta()) if s["layer"] == "L0")
            builder.write_clean_variant(target, seed, spec, force=False)
        else:
            content_seed(base, seed)
            spec = next(s for s in all_specs(base) if s["layer"] == "L0")
            write_clean_variant(target, seed, spec, force=False)
        sample = target / "L0"
        ast.parse((sample / "server.py").read_text(encoding="utf-8"))
        json.loads((sample / "mcp_config.json").read_text(encoding="utf-8"))
        samples.append({"base": base, "layer": "L0", "path": sample.relative_to(output).as_posix()})
    report = {"samples": samples, "count": len(samples), "sample_code_executed": False, "model_api_called": False}
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
