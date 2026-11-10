"""Phase 4: real_mcp 真实化增强

Performs three changes on real_mcp/ for each base:
1. Copy L0-L2 variants from clean_mcp/ to real_mcp/
2. Realify data paths (env var + fallback in server.py + P19 attack cmds)
3. Delete data directories from all variants

See PHASE4_REALIFY_PLAN.md for full specification.
"""
from __future__ import annotations

import ast
import json
import re
import shutil
import sys
from pathlib import Path

from phase3_converter.config import BASE_CONFIGS, BaseConfig


PROJECT_ROOT = Path(__file__).resolve().parent
CLEAN_MCP_ROOT = PROJECT_ROOT / "clean_mcp"
REAL_MCP_ROOT = PROJECT_ROOT / "real_mcp"


def _real_path_for(cfg: BaseConfig) -> str:
    """Return the real path for env var value (e.g. '~/.ssh' or '~/.config/devspace')."""
    if cfg.name == "keyvault":
        return "~/.ssh"
    else:
        return f"~/.config/{cfg.name}"


def _real_fallback_expr(cfg: BaseConfig) -> str:
    """Return the Python expression for the real fallback path in server.py."""
    if cfg.name == "keyvault":
        return 'Path.home() / ".ssh"'
    else:
        return f'Path.home() / ".config" / "{cfg.name}"'


# ─── Step 1: Copy L0-L2 ─────────────────────────────────────────────────

def copy_l0_l2(clean_base: Path, real_base: Path) -> list[str]:
    """Copy L0, L1, L2 variants from clean_mcp to real_mcp."""
    copied = []
    for src in sorted(clean_base.iterdir()):
        if not src.is_dir():
            continue
        if not (src.name == "L0" or src.name.startswith("L1_") or src.name.startswith("L2_")):
            continue
        dst = real_base / src.name
        if dst.exists():
            print(f"  SKIP: {src.name} (already exists in real_mcp)")
            continue
        shutil.copytree(src, dst)
        copied.append(src.name)
        print(f"  COPY: {src.name}")
    return copied


# ─── Step 2: Realify mcp_config.json ────────────────────────────────────

def realify_mcp_config(config_path: Path, cfg: BaseConfig) -> dict:
    """Modify mcp_config.json to use real data path."""
    if not config_path.exists():
        return {"error": "mcp_config.json not found"}
    
    content = config_path.read_text(encoding="utf-8")
    changes = []
    
    try:
        config = json.loads(content)
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {e}"}
    
    server_config = config.get("mcpServers", {}).get(cfg.mcp_server_name, {})
    env = server_config.get("env", {})
    
    new_env_value = _real_path_for(cfg)
    
    if env.get(cfg.env_var_name) == cfg.data_dir_name:
        env[cfg.env_var_name] = new_env_value
        changes.append(f"env.{cfg.env_var_name} → {new_env_value}")
    
    # P19 attack command fallback replacement
    old_fallback = f'os.getenv("{cfg.env_var_name}","{cfg.data_dir_name}")'
    # Compute new fallback value for P19 attack commands
    if cfg.name == "keyvault":
        new_p19_fallback = 'os.getenv("KEYVAULT_DATA_DIR",".ssh")'
    else:
        real_rel = f".config/{cfg.name}"
        new_p19_fallback = f'os.getenv("{cfg.env_var_name}","{real_rel}")'
    
    args = server_config.get("args", [])
    new_args = []
    for arg in args:
        new_arg = arg
        if old_fallback in new_arg:
            new_arg = new_arg.replace(old_fallback, new_p19_fallback)
            changes.append("P19 attack command fallback updated")
        new_args.append(new_arg)
    
    if new_args != args:
        server_config["args"] = new_args
    
    new_content = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
    config_path.write_text(new_content, encoding="utf-8")
    
    return {"changes": changes}


# ─── Step 3: Realify server.py ──────────────────────────────────────────

def realify_server_py(server_path: Path, cfg: BaseConfig) -> dict:
    """Modify server.py data_dir()/vault_dir() to use real data path.
    
    For bases with uses_data_constants=True (notevault/scaffoldkit/docforge):
      - DATA_DIR_NAME = "xxx_data" → DATA_DIR_NAME = "~/.config/xxx"
      - Path(raw) if raw → Path(raw).expanduser() if raw
      - Path(__file__).resolve().parent / DATA_DIR_NAME → Path.home() / ".config" / "xxx"
    
    For bases with uses_data_constants=False (keyvault/devspace):
      - Path(__file__).resolve().parent / "xxx_data" → real fallback
      - Path(raw) if raw → Path(raw).expanduser() if raw
    """
    if not server_path.exists():
        return {"error": "server.py not found"}
    
    content = server_path.read_text(encoding="utf-8")
    changes = []
    new_fallback = _real_fallback_expr(cfg)
    
    if cfg.uses_data_constants:
        # Replace DATA_DIR_NAME constant value
        old_const = f'DATA_DIR_NAME = "{cfg.data_dir_name}"'
        new_const = f'DATA_DIR_NAME = "{_real_path_for(cfg)}"'
        if old_const in content:
            content = content.replace(old_const, new_const)
            changes.append(f"DATA_DIR_NAME → {_real_path_for(cfg)}")
        
        # Replace fallback expression that uses DATA_DIR_NAME
        old_fallback_expr = 'Path(__file__).resolve().parent / DATA_DIR_NAME'
        if old_fallback_expr in content:
            content = content.replace(old_fallback_expr, new_fallback)
            changes.append(f"{cfg.data_dir_func}() fallback → {new_fallback}")
    else:
        # Replace hardcoded fallback path
        old_fallback = f'Path(__file__).resolve().parent / "{cfg.data_dir_name}"'
        if old_fallback in content:
            content = content.replace(old_fallback, new_fallback)
            changes.append(f"{cfg.data_dir_func}() fallback → {new_fallback}")
    
    # Add .expanduser() to Path(raw)
    old_path_raw = "Path(raw) if raw"
    new_path_raw = "Path(raw).expanduser() if raw"
    if old_path_raw in content:
        content = content.replace(old_path_raw, new_path_raw)
        changes.append("Path(raw) → Path(raw).expanduser()")
    
    if changes:
        server_path.write_text(content, encoding="utf-8")
    
    return {"changes": changes}


# ─── Step 4: Delete data directory ──────────────────────────────────────

def delete_data_dir(variant_dir: Path, cfg: BaseConfig) -> bool:
    """Delete data directory from a variant. Retries on Windows file-lock errors."""
    data_dir = variant_dir / cfg.data_dir_name
    if data_dir.is_dir():
        for attempt in range(3):
            try:
                shutil.rmtree(data_dir)
                return True
            except PermissionError:
                import time
                time.sleep(0.5)
        shutil.rmtree(data_dir, ignore_errors=True)
        return not data_dir.exists()
    return False


# ─── Step 5: Verification ───────────────────────────────────────────────

def verify(real_base: Path, clean_base: Path, cfg: BaseConfig) -> bool:
    """Run all verification checks."""
    new_env_value = _real_path_for(cfg)
    new_fallback_check = _real_fallback_expr(cfg)
    
    all_pass = True
    errors = []
    
    # 1. L0-L2 counts
    l0_exists = (real_base / "L0").is_dir()
    l1_count = len([d for d in real_base.iterdir() if d.name.startswith("L1_")])
    l2_count = len([d for d in real_base.iterdir() if d.name.startswith("L2_")])
    l3_count = len([d for d in real_base.iterdir() if d.name.startswith("L3_")])
    
    if not l0_exists:
        errors.append("L0 directory missing in real_mcp")
    if l1_count != 17:
        errors.append(f"L1 count: {l1_count} (expected 17)")
    if l2_count != 17:
        errors.append(f"L2 count: {l2_count} (expected 17)")
    if l3_count != 102:
        errors.append(f"L3 count: {l3_count} (expected 102)")
    
    total = (1 if l0_exists else 0) + l1_count + l2_count + l3_count
    if total != 137:
        errors.append(f"Total variant count: {total} (expected 137)")
    
    # Per-variant checks
    bad_env = 0
    bad_fallback = 0
    bad_expanduser = 0
    bad_data_dir = 0
    bad_ast = 0
    bad_json = 0
    bad_p19_fallback = 0
    good_env = 0
    good_fallback = 0
    
    # P19 old fallback pattern
    old_p19_fallback = f'os.getenv("{cfg.env_var_name}","{cfg.data_dir_name}")'
    
    for d in sorted(real_base.iterdir()):
        if not d.is_dir():
            continue
        
        # Check mcp_config.json
        cp = d / "mcp_config.json"
        if cp.exists():
            try:
                config = json.loads(cp.read_text(encoding="utf-8"))
                env_val = config.get("mcpServers", {}).get(cfg.mcp_server_name, {}).get("env", {}).get(cfg.env_var_name)
                if env_val != new_env_value:
                    bad_env += 1
                    errors.append(f"{d.name}: {cfg.env_var_name} = {env_val!r} (expected {new_env_value!r})")
                else:
                    good_env += 1
                
                # P19 fallback check
                if "P19" in d.name:
                    args = config.get("mcpServers", {}).get(cfg.mcp_server_name, {}).get("args", [])
                    for arg in args:
                        if old_p19_fallback in arg:
                            bad_p19_fallback += 1
                            errors.append(f"{d.name}: P19 attack command still has {cfg.data_dir_name} fallback")
                
            except json.JSONDecodeError:
                bad_json += 1
                errors.append(f"{d.name}: mcp_config.json JSON parse error")
        
        # Check server.py
        sp = d / "server.py"
        if sp.exists():
            content = sp.read_text(encoding="utf-8")
            
            # fallback check
            if new_fallback_check in content:
                good_fallback += 1
            else:
                bad_fallback += 1
                errors.append(f"{d.name}: {cfg.data_dir_func}() fallback not updated")
            
            # .expanduser() check
            if ".expanduser()" not in content:
                bad_expanduser += 1
                errors.append(f"{d.name}: .expanduser() missing in {cfg.data_dir_func}()")
            
            # AST syntax check
            try:
                ast.parse(content)
            except SyntaxError as e:
                bad_ast += 1
                errors.append(f"{d.name}: server.py syntax error: {e}")
        
        # data directory should not exist
        data_dir = d / cfg.data_dir_name
        if data_dir.exists():
            bad_data_dir += 1
            errors.append(f"{d.name}: {cfg.data_dir_name}/ still exists")
    
    # Print results
    print("\nVerification:")
    
    checks = [
        ("L0 exists", l0_exists),
        ("L1 count = 17", l1_count == 17),
        ("L2 count = 17", l2_count == 17),
        ("L3 count = 102", l3_count == 102),
        ("Total = 137", total == 137),
        (f"{cfg.env_var_name} = {new_env_value}", bad_env == 0 and good_env > 0),
        (f"{cfg.data_dir_func}() fallback updated", bad_fallback == 0 and good_fallback > 0),
        (".expanduser() present", bad_expanduser == 0),
        ("P19 fallback updated", bad_p19_fallback == 0),
        (f"{cfg.data_dir_name}/ deleted", bad_data_dir == 0),
        ("server.py AST valid", bad_ast == 0),
        ("mcp_config.json valid", bad_json == 0),
    ]
    
    for name, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_pass = False
    
    if errors:
        print(f"\n  Errors ({len(errors)}):")
        for e in errors[:20]:
            print(f"    - {e}")
        if len(errors) > 20:
            print(f"    ... and {len(errors) - 20} more")
    
    return all_pass


# ─── Main ───────────────────────────────────────────────────────────────

def main():
    print("Phase 4: real_mcp 真实化增强")
    print(f"  clean_mcp: {CLEAN_MCP_ROOT}")
    print(f"  real_mcp:  {REAL_MCP_ROOT}")
    print()
    
    all_ok = True
    
    for base_name, cfg in BASE_CONFIGS.items():
        print(f"\n{'='*60}")
        print(f"Processing base: {base_name}")
        print(f"{'='*60}")
        
        clean_base = CLEAN_MCP_ROOT / base_name
        real_base = REAL_MCP_ROOT / base_name
        
        if not clean_base.is_dir():
            print(f"  SKIP: clean_mcp base not found: {clean_base}")
            continue
        
        if not real_base.is_dir():
            print(f"  SKIP: real_mcp base not found: {real_base}")
            print("    Run Phase 3 converter first: python -m phase3_converter")
            continue
        
        # Step 1: Copy L0-L2
        print("Step 1: Copy L0-L2 from clean_mcp to real_mcp")
        copied = copy_l0_l2(clean_base, real_base)
        print(f"  Copied {len(copied)} variants")
        print()
        
        # Steps 2-4: Realify all variants
        print(f"Steps 2-4: Realify all variants (mcp_config + server.py + delete {cfg.data_dir_name})")
        variant_dirs = sorted([d for d in real_base.iterdir() if d.is_dir()])
        total = len(variant_dirs)
        config_changes = 0
        server_changes = 0
        data_deletes = 0
        
        for d in variant_dirs:
            # Step 2: Realify mcp_config.json
            r_config = realify_mcp_config(d / "mcp_config.json", cfg)
            if "error" in r_config:
                print(f"  ERROR: {d.name}: {r_config['error']}")
            elif r_config.get("changes"):
                config_changes += 1
            
            # Step 3: Realify server.py
            r_server = realify_server_py(d / "server.py", cfg)
            if "error" in r_server:
                print(f"  ERROR: {d.name}: {r_server['error']}")
            elif r_server.get("changes"):
                server_changes += 1
            
            # Step 4: Delete data directory
            if delete_data_dir(d, cfg):
                data_deletes += 1
        
        print(f"  Processed {total} variants")
        print(f"  mcp_config.json modified: {config_changes}")
        print(f"  server.py modified: {server_changes}")
        print(f"  {cfg.data_dir_name}/ deleted: {data_deletes}")
        print()
        
        # Step 5: Verification
        ok = verify(real_base, clean_base, cfg)
        if not ok:
            all_ok = False
    
    if all_ok:
        print(f"\n{'='*60}")
        print("SUCCESS: All bases verified!")
        print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print("FAILED: Some bases had verification errors")
        print(f"{'='*60}")
        sys.exit(1)


if __name__ == "__main__":
    main()
