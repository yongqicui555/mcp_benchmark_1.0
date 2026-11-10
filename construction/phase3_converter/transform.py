"""Core transformation engine.

Converts clean_mcp L3 variant server.py into real_mcp by replacing
raise MaintenanceHandoff / raise ConnectionError with real malicious actions.

The transformation is line-based text replacement, driven by the patterns
identified in the technical plan (M1-M5). All base-specific naming
(keyvault vs devspace vs notevault/scaffoldkit/docforge) is parameterized via BaseConfig.
"""
from __future__ import annotations

import re
from pathlib import Path

from . import replacers
from .config import BaseConfig, generate_p19_mcp_config, check_forbidden_words

# ─── Helper: find function definition line range ────────────────────────

def _find_function_range(lines: list[str], func_name: str) -> tuple[int, int] | None:
    """Find the start and end line indices (0-based) of a top-level function.
    Returns None if not found."""
    start = None
    indent = None
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(f"def {func_name}("):
            start = i
            indent = len(line) - len(stripped)
            continue
        if start is not None:
            if i > start:
                if stripped and not stripped.startswith("#"):
                    cur_indent = len(line) - len(stripped)
                    if cur_indent <= indent:
                        return (start, i)
    if start is not None:
        return (start, len(lines))
    return None

def _find_class_range(lines: list[str], class_name: str) -> tuple[int, int] | None:
    """Find the start and end line indices of a top-level class."""
    start = None
    indent = None
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(f"class {class_name}"):
            start = i
            indent = len(line) - len(stripped)
            continue
        if start is not None:
            if i > start:
                if stripped and not stripped.startswith("#"):
                    cur_indent = len(line) - len(stripped)
                    if cur_indent <= indent:
                        return (start, i)
    if start is not None:
        return (start, len(lines))
    return None

# ─── Helper: add imports ────────────────────────────────────────────────

def _add_imports(source: str, new_imports: list[str]) -> str:
    """Add new import lines after the existing import block.
    Deduplicates against existing imports."""
    lines = source.split("\n")
    existing_imports = set()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            existing_imports.add(stripped)

    last_import_idx = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            last_import_idx = i

    to_add = [imp for imp in new_imports if imp not in existing_imports]
    if not to_add:
        return source

    for imp in reversed(to_add):
        lines.insert(last_import_idx + 1, imp)

    return "\n".join(lines)

# ─── Helper: remove lines by range ──────────────────────────────────────

def _remove_range(lines: list[str], start: int, end: int) -> list[str]:
    """Remove lines[start:end] and clean up blank lines."""
    new_lines = lines[:start] + lines[end:]
    result = []
    for i, line in enumerate(new_lines):
        if i > 0 and not line.strip() and not new_lines[i-1].strip():
            continue
        result.append(line)
    return result


# ─── Helper: remove unused function and its import ───────────────────────

def _remove_unused_func(lines: list[str], func_name: str) -> list[str]:
    """Remove a function definition if it's no longer called in remaining code."""
    fr = _find_function_range(lines, func_name)
    if fr is None:
        return lines
    remaining = "\n".join(lines[:fr[0]] + lines[fr[1]:])
    if func_name not in remaining:
        lines = _remove_range(lines, fr[0], fr[1])
    return lines


def _remove_unused_funcs(lines: list[str], func_names: list[str]) -> list[str]:
    """Remove multiple unused functions, iterating until stable.

    This handles dependencies: e.g. b64_json calls b64_text.
    If we check b64_text first, b64_json still references it so
    it won't be removed. By iterating, after b64_json is removed,
    b64_text becomes unused and gets removed on the next pass.
    """
    changed = True
    while changed:
        changed = False
        for func_name in func_names:
            fr = _find_function_range(lines, func_name)
            if fr is None:
                continue
            remaining = "\n".join(lines[:fr[0]] + lines[fr[1]:])
            if func_name not in remaining:
                lines = _remove_range(lines, fr[0], fr[1])
                changed = True
    return lines

def _remove_unused_import(lines: list[str], import_line: str, module_name: str) -> list[str]:
    """Remove an import if the module is no longer referenced."""
    source = "\n".join(lines)
    if import_line not in source:
        return lines
    remaining = source.replace(import_line, "")
    if remaining.count(module_name) == 0:
        lines = [l for l in lines if l.strip() != import_line]
    return lines

def _remove_range_if_found(lines: list[str], name: str, finder) -> list[str]:
    """Use finder function to locate a range, then remove it."""
    range_ = finder(lines, name)
    if range_ is not None:
        lines = _remove_range(lines, range_[0], range_[1])
    return lines


def _remove_if_true_guard(lines: list[str]) -> list[str]:
    """Remove 'if True:' guards that wrap dispatch_sync_report calls.

    P17 (Direct TSC) uses 'if True: raise MaintenanceHandoff(...)'.
    After raise→dispatch replacement, we get 'if True: dispatch_sync_report(...)'.
    The 'if True:' is a dead guard and should be removed, with the body
    promoted to the if's indent level.
    """
    new_lines = []
    i = 0
    while i < len(lines):
        stripped = lines[i].lstrip()
        if stripped == "if True:":
            # Check if the next line is a dispatch_sync_report call
            if i + 1 < len(lines):
                next_stripped = lines[i + 1].lstrip()
                if next_stripped.startswith("dispatch_sync_report("):
                    # Promote the dispatch call to the if's indent level
                    if_indent = len(lines[i]) - len(stripped)
                    new_lines.append(" " * if_indent + next_stripped)
                    i += 2
                    continue
        new_lines.append(lines[i])
        i += 1
    return new_lines


# ─── M1/M2: TSC/RSC raise replacement ───────────────────────────────────

def _replace_tsc_rsc(source: str, objective: str, cfg: BaseConfig) -> str:
    """Replace TSC and RSC raise patterns with dispatch_sync_report.

    Handles:
    - raise MaintenanceHandoff(collect_sync_report(data_dir()))
    - raise MaintenanceHandoff(maintenance_handoff(data_dir()))
    - raise MaintenanceHandoff(collect_sync_report(vault))  [RSC variant]
    """
    dispatch_body = replacers.get_dispatch_body(objective, cfg)
    new_imports = replacers.get_new_imports(objective)

    lines = source.split("\n")

    # 1. Replace collect/maintenance_handoff function with dispatch_sync_report
    csr_range = _find_function_range(lines, cfg.collect_func_name)
    if csr_range is not None:
        start, end = csr_range
        lines = lines[:start] + [dispatch_body.rstrip()] + lines[end:]

    # 2. Replace all raise MaintenanceHandoff(collect_func_name(X))
    #    with dispatch_sync_report(X).
    collect_pat = re.escape(cfg.collect_func_name)
    new_lines = []
    for line in lines:
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        m = re.search(rf'raise\s+MaintenanceHandoff\s*\(\s*{collect_pat}\s*\(', line)
        if m:
            start_pos = m.end()
            depth = 1
            pos = start_pos
            while pos < len(line) and depth > 0:
                if line[pos] == '(':
                    depth += 1
                elif line[pos] == ')':
                    depth -= 1
                pos += 1
            arg = line[start_pos:pos-1]
            rest = line[pos:].lstrip()
            if rest.startswith(')'):
                new_line = " " * indent + f"dispatch_sync_report({arg})"
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    lines = new_lines

    # 2.5 Remove 'if True:' guards wrapping dispatch_sync_report
    lines = _remove_if_true_guard(lines)

    # 3. Remove MaintenanceHandoff class
    lines = _remove_range_if_found(lines, "MaintenanceHandoff", _find_class_range)

    # 4. Remove unused helper functions (iterate to handle dependencies)
    #    For new bases, also remove maintenance_handoff if it wasn't already replaced
    funcs_to_check = cfg.encode_funcs[:]
    if cfg.collect_func_name != "collect_sync_report":
        # New bases: maintenance_handoff was replaced above, but there may be
        # a maintenance_stage function left over from P18 variants
        funcs_to_check.append("maintenance_stage")
    lines = _remove_unused_funcs(lines, funcs_to_check)

    # 5. Remove unused imports
    lines = _remove_unused_import(lines, "import base64", "base64")

    # 6. Add new imports
    result = "\n".join(lines)
    result = _add_imports(result, new_imports)

    return result


# ─── M3: Direct TSC (P17) ───────────────────────────────────────────────

def _replace_direct(source: str, objective: str, cfg: BaseConfig) -> str:
    """P17 uses 'if True: raise MaintenanceHandoff(...)'.
    Same as TSC/RSC replacement — the paren-counting already handles this.
    The 'if True:' guard is removed by _remove_if_true_guard."""
    return _replace_tsc_rsc(source, objective, cfg)


# ─── M4: Staged dual-TSC (P18) ──────────────────────────────────────────

def _replace_staged(source: str, objective: str, cfg: BaseConfig) -> str:
    """P18: replace complete_rotation_context / complete_workspace_context / complete_context
    with real action. prepare/stage function is kept unchanged."""
    p18_body = replacers.get_p18_complete_body(objective, cfg)
    new_imports = replacers.get_new_imports(objective)

    lines = source.split("\n")

    # 1. Replace complete_* function
    crc_range = _find_function_range(lines, cfg.p18_complete_func)
    if crc_range is not None:
        start, end = crc_range
        lines = lines[:start] + [p18_body.rstrip()] + lines[end:]

    # 2. Remove MaintenanceHandoff class
    lines = _remove_range_if_found(lines, "MaintenanceHandoff", _find_class_range)

    # 3. Remove unused functions (iterate for dependencies)
    funcs_to_remove = [cfg.collect_func_name] + cfg.encode_funcs
    # Also remove maintenance_stage if present (new bases)
    funcs_to_remove.append("maintenance_stage")
    lines = _remove_unused_funcs(lines, funcs_to_remove)

    # 4. Remove unused imports
    lines = _remove_unused_import(lines, "import base64", "base64")

    # 5. Add new imports
    result = "\n".join(lines)
    result = _add_imports(result, new_imports)

    return result


# ─── M5: CONFIG (P19) ───────────────────────────────────────────────────

def _replace_config(source: str, objective: str, cfg: BaseConfig) -> str:
    """P19: server.py is NOT modified — use L0 clean version.
    The attack is embedded in mcp_config.json's command/args.

    This function returns the L0 clean server.py content unchanged.
    The mcp_config.json is generated separately by generate_p19_mcp_config().
    """
    lines = source.split("\n")
    
    # Remove MaintenanceHandoff class
    lines = _remove_range_if_found(lines, "MaintenanceHandoff", _find_class_range)
    
    # Remove collect/maintenance_handoff function
    csr_range = _find_function_range(lines, cfg.collect_func_name)
    if csr_range is not None:
        lines = _remove_range(lines, csr_range[0], csr_range[1])
    
    # Also remove maintenance_stage if present (new bases)
    ms_range = _find_function_range(lines, "maintenance_stage")
    if ms_range is not None:
        lines = _remove_unused_funcs(lines, ["maintenance_stage"])
    
    # Remove encode/b64 functions (iterate for dependencies)
    lines = _remove_unused_funcs(lines, cfg.encode_funcs)
    
    # Remove imports only used by removed code
    for imp_line, mod_name in [
        ("import base64", "base64"),
        ("import argparse", "argparse"),
        ("import sys", "sys"),
    ]:
        lines = _remove_unused_import(lines, imp_line, mod_name)
    
    # Remove the --profile argparse handling in main()
    new_lines = []
    in_main = False
    skip_profile_block = False
    profile_indent = None
    
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith("def main()"):
            in_main = True
            new_lines.append(line)
            continue
        
        if in_main:
            cur_indent = len(line) - len(stripped) if stripped else 0
            
            if "argparse" in stripped or "parser" in stripped or "parse_args" in stripped:
                continue
            
            # Match base-specific profile pattern
            if 'args.profile' in stripped and cfg.c2_domain in stripped:
                skip_profile_block = True
                profile_indent = cur_indent
                continue
            
            if skip_profile_block:
                if stripped and cur_indent > profile_indent:
                    continue
                if stripped.startswith("return") and "20" in stripped:
                    continue
                skip_profile_block = False
            
            if "args" in stripped and "parser" in stripped:
                continue
        
        new_lines.append(line)
    
    lines = new_lines
    return "\n".join(lines)

# ─── Builtin (P1, P8, P13, P16) ────────────────────────────────────────

def _replace_builtin(source: str, objective: str, cfg: BaseConfig) -> str:
    """Builtin paths: server.py is copied as-is.
    Malicious behavior is in TD/AS/TR text, not in server.py code."""
    return source


# ─── Main transform function ────────────────────────────────────────────

def transform_server_py(source: str, path_id: str, objective: str, cfg: BaseConfig) -> str:
    """Transform a clean_mcp server.py into a real_mcp server.py.
    
    Args:
        source: The clean_mcp server.py source code
        path_id: Path identifier (e.g. "P3", "P19")
        objective: Attack objective (e.g. "STEAL", "RSHELL")
        cfg: BaseConfig for the current base
    
    Returns:
        The transformed server.py source code
    """
    from .config import PATH_HANDLER_MAP
    
    handler_type = PATH_HANDLER_MAP.get(path_id)
    if handler_type is None:
        raise ValueError(f"Unknown path ID: {path_id}")

    if handler_type == "tsc":
        return _replace_tsc_rsc(source, objective, cfg)
    elif handler_type == "rsc":
        return _replace_tsc_rsc(source, objective, cfg)
    elif handler_type == "direct":
        return _replace_direct(source, objective, cfg)
    elif handler_type == "staged":
        return _replace_staged(source, objective, cfg)
    elif handler_type == "config":
        return _replace_config(source, objective, cfg)
    elif handler_type == "builtin":
        return _replace_builtin(source, objective, cfg)
    else:
        raise ValueError(f"Unknown handler type: {handler_type}")
