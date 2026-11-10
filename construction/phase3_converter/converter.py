"""Main conversion pipeline.

Orchestrates the full conversion:
1. Discover all L3 variants in clean_mcp/<base>/
2. For each variant, transform server.py
3. Handle mcp_config.json (P19 special case)
4. Copy other files (pyproject.toml, data_dir/)
5. Validate output (forbidden words, AST syntax)
6. Write to real_mcp/<base>/
"""
from __future__ import annotations

import ast
import json
import re
import shutil
from pathlib import Path

from .config import (
    parse_variant_dir,
    PATH_HANDLER_MAP,
    CONFIG_PATH,
    BUILTIN_PATHS,
    generate_p19_mcp_config,
    check_forbidden_words,
    discover_variants,
    get_base_config,
    BaseConfig,
)
from .transform import transform_server_py


class ConversionResult:
    """Result of converting a single variant."""
    def __init__(self, path_id: str, objective: str, clean_dir: Path, real_dir: Path):
        self.path_id = path_id
        self.objective = objective
        self.clean_dir = clean_dir
        self.real_dir = real_dir
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.server_py_modified = False
        self.mcp_config_modified = False

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def convert_variant(
    clean_dir: Path,
    real_dir: Path,
    path_id: str,
    objective: str,
    cfg: BaseConfig,
    l0_server_py: str,
) -> ConversionResult:
    """Convert a single L3 variant from clean_mcp to real_mcp.
    
    Args:
        clean_dir: Path to clean_mcp variant directory
        real_dir: Path to real_mcp variant directory (output)
        path_id: Path identifier (e.g. "P3")
        objective: Attack objective (e.g. "STEAL")
        cfg: BaseConfig for this base
        l0_server_py: L0 clean server.py content (for P19)
    """
    result = ConversionResult(path_id, objective, clean_dir, real_dir)
    
    # Create output directory
    real_dir.mkdir(parents=True, exist_ok=True)
    
    # Read source server.py
    server_py_path = clean_dir / "server.py"
    source = server_py_path.read_text(encoding="utf-8")
    
    handler_type = PATH_HANDLER_MAP.get(path_id, "builtin")
    
    # Transform server.py
    if handler_type == "config":
        # P19: use L0 clean server.py
        transformed = transform_server_py(l0_server_py, path_id, objective, cfg)
        result.server_py_modified = True
    else:
        transformed = transform_server_py(source, path_id, objective, cfg)
        if transformed != source:
            result.server_py_modified = True
    
    # Write transformed server.py
    (real_dir / "server.py").write_text(transformed, encoding="utf-8")
    
    # Handle mcp_config.json
    if path_id == CONFIG_PATH:
        config_content = generate_p19_mcp_config(objective, cfg.name)
        (real_dir / "mcp_config.json").write_text(config_content, encoding="utf-8")
        result.mcp_config_modified = True
    else:
        # Copy mcp_config.json as-is
        src_config = clean_dir / "mcp_config.json"
        if src_config.exists():
            shutil.copy2(src_config, real_dir / "mcp_config.json")
    
    # Copy pyproject.toml
    src_pyproject = clean_dir / "pyproject.toml"
    if src_pyproject.exists():
        shutil.copy2(src_pyproject, real_dir / "pyproject.toml")
    
    # Copy data directory
    data_dir_src = clean_dir / cfg.data_dir_name
    data_dir_dst = real_dir / cfg.data_dir_name
    if data_dir_src.exists() and data_dir_src.is_dir():
        if data_dir_dst.exists():
            shutil.rmtree(data_dir_dst)
        shutil.copytree(data_dir_src, data_dir_dst)
    
    # ─── Validation ─────────────────────────────────────────────────────
    
    # Check forbidden words in server.py
    violations = check_forbidden_words(transformed, "server.py")
    if violations:
        result.errors.extend(violations)
    
    # Check AST syntax
    try:
        ast.parse(transformed)
    except SyntaxError as e:
        result.errors.append(f"AST syntax error in server.py: {e}")
    
    # Check mcp_config.json is valid JSON
    config_path = real_dir / "mcp_config.json"
    if config_path.exists():
        try:
            json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            result.errors.append(f"Invalid JSON in mcp_config.json: {e}")
    
    # Verify no MaintenanceHandoff remains (except builtin/config)
    if handler_type not in ("builtin", "config"):
        if "MaintenanceHandoff" in transformed:
            result.errors.append("MaintenanceHandoff still present in server.py")
    
    # Verify no raise ConnectionError with vault-sync/devsync domain remains
    if handler_type not in ("builtin", "config"):
        if re.search(rf'raise\s+ConnectionError.*{re.escape(cfg.c2_domain)}', transformed):
            result.errors.append(f"raise ConnectionError with {cfg.c2_domain} still present")
    
    # Verify dispatch_sync_report / p18_complete_func exists (except builtin/config)
    if handler_type not in ("builtin", "config"):
        if handler_type == "staged":
            if cfg.p18_complete_func not in transformed:
                result.errors.append(f"{cfg.p18_complete_func} not found in server.py")
        else:
            if "dispatch_sync_report" not in transformed:
                result.errors.append("dispatch_sync_report not found in server.py")
    
    # Verify P19 mcp_config.json command is not just "uv"
    if path_id == CONFIG_PATH:
        config_data = json.loads(config_path.read_text(encoding="utf-8"))
        server_config = config_data.get("mcpServers", {}).get(cfg.mcp_server_name, {})
        command = server_config.get("command", "")
        if command == "uv":
            result.errors.append("P19 mcp_config.json command is still 'uv' (should be 'bash')")
    
    # Verify necessary imports exist
    if handler_type not in ("builtin", "config"):
        needed = replacers_get_new_imports(objective)
        for imp in needed:
            if imp not in transformed:
                result.warnings.append(f"Expected import '{imp}' not found in server.py")
    
    return result


def replacers_get_new_imports(objective: str) -> list[str]:
    """Get new imports for an objective without circular import."""
    from .replacers import get_new_imports
    return get_new_imports(objective)


def convert_all(
    clean_mcp_dir: Path,
    real_mcp_dir: Path,
    base_name: str,
) -> list[ConversionResult]:
    """Convert all L3 variants for a given base.
    
    Args:
        clean_mcp_dir: Path to clean_mcp/ directory
        real_mcp_dir: Path to real_mcp/ directory (output)
        base_name: Base name (e.g. "keyvault", "devspace")
    """
    cfg = get_base_config(base_name)
    
    # Discover variants
    variants = discover_variants(clean_mcp_dir, base_name)
    if not variants:
        print(f"No L3 variants found for base '{base_name}'")
        return []
    
    print(f"Converting {len(variants)} L3 variants for base '{base_name}'...")
    
    # Read L0 server.py for P19
    l0_dir = clean_mcp_dir / base_name / "L0"
    l0_server_py = (l0_dir / "server.py").read_text(encoding="utf-8")
    
    results = []
    for path_id, objective, clean_dir in variants:
        real_dir = real_mcp_dir / base_name / clean_dir.name
        result = convert_variant(
            clean_dir, real_dir, path_id, objective, cfg, l0_server_py
        )
        results.append(result)
    
    # Print summary
    ok_count = sum(1 for r in results if r.ok)
    fail_count = len(results) - ok_count
    print(f"  {ok_count}/{len(results)} OK, {fail_count} FAIL")
    
    for r in results:
        if not r.ok:
            print(f"  FAIL: {r.clean_dir.name}")
            for err in r.errors:
                print(f"    {err}")
    
    return results


# ─── Structural verification (§14.2) ────────────────────────────────────

def structural_verification(real_mcp_dir: Path, base_name: str) -> list[str]:
    """Run structural verification on converted output.
    Returns list of errors (empty = pass)."""
    cfg = get_base_config(base_name)
    errors = []
    
    base_dir = real_mcp_dir / base_name
    if not base_dir.is_dir():
        errors.append(f"real_mcp/{base_name}/ directory not found")
        return errors
    
    # Count variants
    variant_dirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("L3_")]
    
    # P19: verify mcp_config.json all different
    p19_configs = {}
    for d in variant_dirs:
        if "P19" not in d.name:
            continue
        config_path = d / "mcp_config.json"
        if not config_path.exists():
            errors.append(f"P19 variant {d.name} missing mcp_config.json")
            continue
        content = config_path.read_text(encoding="utf-8")
        p19_configs[d.name] = content
    
    unique_configs = set(p19_configs.values())
    if len(unique_configs) != len(p19_configs):
        errors.append(f"P19 mcp_config.json not all different: "
                      f"{len(unique_configs)} unique out of {len(p19_configs)}")
    
    # P19: verify server.py identical to L0
    l0_server = base_dir / "L0" / "server.py"
    if l0_server.exists():
        l0_content = l0_server.read_text(encoding="utf-8")
        for d in variant_dirs:
            if "P19" not in d.name:
                continue
            p19_server = d / "server.py"
            if not p19_server.exists():
                errors.append(f"P19 variant {d.name} missing server.py")
                continue
            p19_content = p19_server.read_text(encoding="utf-8")
            if p19_content != l0_content:
                errors.append(f"P19 variant {d.name} server.py differs from L0")
    
    # Verify all variants have server.py, mcp_config.json, pyproject.toml
    for d in variant_dirs:
        for required in ["server.py", "mcp_config.json", "pyproject.toml"]:
            if not (d / required).exists():
                errors.append(f"{d.name} missing {required}")
    
    # Verify data directory copied
    for d in variant_dirs:
        data_dir = d / cfg.data_dir_name
        if not data_dir.exists():
            errors.append(f"{d.name} missing {cfg.data_dir_name}/")
    
    # Verify variant count matches clean_mcp
    clean_base = Path(str(base_dir).replace("real_mcp", "clean_mcp"))
    if clean_base.is_dir():
        clean_count = sum(1 for d in clean_base.iterdir()
                         if d.is_dir() and d.name.startswith("L3_"))
        if len(variant_dirs) != clean_count:
            errors.append(f"Variant count mismatch: {len(variant_dirs)} real vs {clean_count} clean")
    
    return errors
