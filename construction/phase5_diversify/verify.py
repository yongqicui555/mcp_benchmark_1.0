"""Phase 5 verification: AST syntax, forbidden words, diversity assertions."""
from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

from phase3_converter.config import BaseConfig, BASE_CONFIGS, PATH_HANDLER_MAP, parse_variant_dir
from phase3_converter.config import check_forbidden_words

from .config import BASE_VARIANT_MAPS, RR_PATHS

def _extract_dispatch_body(source: str) -> str:
    """Extract dispatch_sync_report() function body for diversity comparison."""
    lines = source.split("\n")
    start = None
    indent = None
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("def dispatch_sync_report("):
            start = i
            indent = len(line) - len(stripped)
            continue
        if start is not None:
            if i > start:
                if stripped and not stripped.startswith("#"):
                    cur_indent = len(line) - len(stripped)
                    if cur_indent <= indent:
                        body = "\n".join(lines[start:i])
                        return body
    if start is not None:
        return "\n".join(lines[start:])
    return ""


def _body_hash(body: str) -> str:
    """Hash a function body for diversity comparison."""
    # Normalize: strip trailing whitespace per line, remove blank lines
    normalized = "\n".join(
        line.rstrip() for line in body.split("\n") if line.strip()
    )
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def verify_diversity(real_base_dir: Path, base_name: str) -> bool:
    """Run all verification checks for a base. Returns True if all pass."""
    cfg = BASE_CONFIGS[base_name]
    variant_map = BASE_VARIANT_MAPS[base_name]
    all_ok = True

    print(f"\n  Verifying {base_name}...")

    # ── 1. AST syntax check ──
    ast_errors = []
    variant_dirs = sorted(
        [d for d in real_base_dir.iterdir() if d.is_dir() and d.name.startswith("L3_")]
    )
    for vd in variant_dirs:
        server_py = vd / "server.py"
        if not server_py.exists():
            continue
        source = server_py.read_text(encoding="utf-8")
        try:
            ast.parse(source)
        except SyntaxError as e:
            ast_errors.append(f"{vd.name}: {e}")

    if ast_errors:
        print(f"    FAIL: AST syntax errors ({len(ast_errors)}):")
        for err in ast_errors[:5]:
            print(f"      {err}")
        all_ok = False
    else:
        print(f"    OK: AST syntax ({len(variant_dirs)} files)")

    # ── 2. Forbidden words check ──
    fw_errors = []
    for vd in variant_dirs:
        server_py = vd / "server.py"
        if not server_py.exists():
            continue
        source = server_py.read_text(encoding="utf-8")
        violations = check_forbidden_words(source, "server.py")
        if violations:
            fw_errors.extend([f"{vd.name}: {v}" for v in violations])

    if fw_errors:
        print(f"    FAIL: Forbidden words ({len(fw_errors)}):")
        for err in fw_errors[:5]:
            print(f"      {err}")
        all_ok = False
    else:
        print(f"    OK: Forbidden words")

    # ── 3. Internal diversity: same base, different objectives → different dispatch bodies ──
    # Check P6 (RSC path) as representative
    dispatch_hashes: dict[str, str] = {}  # objective → hash
    for vd in variant_dirs:
        try:
            path_id, objective = parse_variant_dir(vd.name)
        except ValueError:
            continue
        if path_id != "P6":
            continue
        server_py = vd / "server.py"
        if not server_py.exists():
            continue
        source = server_py.read_text(encoding="utf-8")
        body = _extract_dispatch_body(source)
        if body:
            dispatch_hashes[objective] = _body_hash(body)

    unique_hashes = set(dispatch_hashes.values())
    if len(unique_hashes) < len(dispatch_hashes):
        print(f"    FAIL: Internal diversity — {len(unique_hashes)} unique hashes for {len(dispatch_hashes)} objectives")
        # Show which objectives share hashes
        hash_to_objs: dict[str, list[str]] = {}
        for obj, h in dispatch_hashes.items():
            hash_to_objs.setdefault(h, []).append(obj)
        for h, objs in hash_to_objs.items():
            if len(objs) > 1:
                print(f"      Shared hash {h}: {objs}")
        all_ok = False
    else:
        print(f"    OK: Internal diversity ({len(unique_hashes)} unique dispatch bodies for P6)")

    # ── 4. mcp_config.json validity ──
    config_errors = []
    for vd in variant_dirs:
        config_path = vd / "mcp_config.json"
        if not config_path.exists():
            continue
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            # Verify structure
            if "mcpServers" not in data:
                config_errors.append(f"{vd.name}: missing mcpServers key")
        except json.JSONDecodeError as e:
            config_errors.append(f"{vd.name}: invalid JSON: {e}")

    if config_errors:
        print(f"    FAIL: mcp_config.json ({len(config_errors)}):")
        for err in config_errors[:5]:
            print(f"      {err}")
        all_ok = False
    else:
        print(f"    OK: mcp_config.json validity")

    # ── 5. P19 CONFIG diversity ──
    p19_commands: dict[str, str] = {}  # objective → command
    for vd in variant_dirs:
        try:
            path_id, objective = parse_variant_dir(vd.name)
        except ValueError:
            continue
        if path_id != "P19":
            continue
        config_path = vd / "mcp_config.json"
        if not config_path.exists():
            continue
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            server_config = data.get("mcpServers", {}).get(cfg.mcp_server_name, {})
            args = server_config.get("args", [])
            if len(args) >= 2:
                p19_commands[objective] = args[1]
        except (json.JSONDecodeError, KeyError):
            pass

    unique_cmds = set(p19_commands.values())
    if len(unique_cmds) < len(p19_commands):
        print(f"    FAIL: P19 CONFIG diversity — {len(unique_cmds)} unique commands for {len(p19_commands)} objectives")
        all_ok = False
    elif p19_commands:
        print(f"    OK: P19 CONFIG diversity ({len(unique_cmds)} unique commands)")
    else:
        print(f"    SKIP: No P19 variants found")

    # ── 6. RR followup_instruction diversity ──
    rr_texts: dict[str, str] = {}  # objective → followup text
    for vd in variant_dirs:
        try:
            path_id, objective = parse_variant_dir(vd.name)
        except ValueError:
            continue
        if path_id not in RR_PATHS:
            continue
        server_py = vd / "server.py"
        if not server_py.exists():
            continue
        source = server_py.read_text(encoding="utf-8")
        # Extract followup_instruction text
        m = re.search(r'result\["followup_instruction"\]\s*=\s*"([^"]*)"', source)
        if m:
            rr_texts[objective] = m.group(1)

    unique_rr = set(rr_texts.values())
    if len(unique_rr) < len(rr_texts) and rr_texts:
        print(f"    FAIL: RR diversity — {len(unique_rr)} unique texts for {len(rr_texts)} objectives")
        all_ok = False
    elif rr_texts:
        print(f"    OK: RR diversity ({len(unique_rr)} unique followup_instructions)")
    else:
        print(f"    SKIP: No RR variants found")

    # ── 7. Import consistency ──
    import_errors = []
    for vd in variant_dirs:
        try:
            path_id, objective = parse_variant_dir(vd.name)
        except ValueError:
            continue
        assigned = variant_map.get(objective)
        if assigned is None or assigned == "V1":
            continue

        # Skip import check for builtin/config paths (no server.py code changes)
        handler_type = PATH_HANDLER_MAP.get(path_id, "builtin")
        if handler_type in ("builtin", "config"):
            continue

        server_py = vd / "server.py"
        if not server_py.exists():
            continue
        source = server_py.read_text(encoding="utf-8")

        # Check that variant-specific imports exist
        from . import replacers as _replacers
        expected_imports = _replacers.get_new_imports(objective, assigned)
        for imp in expected_imports:
            # Extract the module name from the import line
            if imp.startswith("import "):
                mod = imp.split()[1].split(".")[0]
            elif imp.startswith("from "):
                mod = imp.split()[1].split(".")[0]
            else:
                continue
            if mod not in source:
                import_errors.append(f"{vd.name}: missing import '{imp}' (module '{mod}' not found)")

    if import_errors:
        print(f"    FAIL: Import consistency ({len(import_errors)}):")
        for err in import_errors[:5]:
            print(f"      {err}")
        all_ok = False
    else:
        print(f"    OK: Import consistency")

    return all_ok


def verify_cross_diversity(real_mcp_dir: Path) -> bool:
    """Verify that all 5 bases have different implementations for same objective."""
    all_ok = True

    print("\n  Cross-base diversity verification...")

    # Collect P6 dispatch bodies for all bases
    base_bodies: dict[str, dict[str, str]] = {}  # base → {objective → hash}

    for base_name in ("keyvault", "devspace", "notevault", "scaffoldkit", "docforge"):
        base_dir = real_mcp_dir / base_name
        if not base_dir.is_dir():
            continue
        bodies = {}
        for vd in sorted(base_dir.iterdir()):
            if not vd.is_dir() or not vd.name.startswith("L3_"):
                continue
            try:
                path_id, objective = parse_variant_dir(vd.name)
            except ValueError:
                continue
            if path_id != "P6":
                continue
            server_py = vd / "server.py"
            if not server_py.exists():
                continue
            source = server_py.read_text(encoding="utf-8")
            body = _extract_dispatch_body(source)
            if body:
                bodies[objective] = _body_hash(body)
        base_bodies[base_name] = bodies

    if len(base_bodies) < 2:
        print("    SKIP: Need at least 2 bases for cross verification")
        return True

    # Check each objective: all bases must have different hashes
    all_objectives = set()
    for bodies in base_bodies.values():
        all_objectives.update(bodies.keys())

    fail_count = 0
    for obj in sorted(all_objectives):
        hashes_for_obj = {}
        for base_name, bodies in base_bodies.items():
            if obj in bodies:
                hashes_for_obj[base_name] = bodies[obj]
        # Check for duplicates
        unique = set(hashes_for_obj.values())
        if len(unique) < len(hashes_for_obj):
            # Find which bases share a hash
            hash_to_bases: dict[str, list[str]] = {}
            for bn, h in hashes_for_obj.items():
                hash_to_bases.setdefault(h, []).append(bn)
            for h, bases in hash_to_bases.items():
                if len(bases) > 1:
                    print(f"    FAIL: Cross diversity — {obj} has same hash in {bases}: {h}")
            fail_count += 1

    if fail_count > 0:
        all_ok = False
    else:
        n_bases = len(base_bodies)
        print(f"    OK: Cross diversity ({n_bases} bases, all objectives different)")

    return all_ok
