"""Phase 5 transform: replace homogeneous payloads with diverse variants.

Operates on real_mcp/ output (post phase3_converter + phase4_realify).
Does NOT touch clean_mcp/.

Five injection mechanisms:
1. TSC/RSC/Direct: replace dispatch_sync_report() function body + imports
2. Staged (P18): replace complete_*_context() function body + imports
3. RR (P8/P11/P12/P13/P16): replace followup_instruction + next_workflow_step + required_host_actions
4. TD (P1): replace command text in @mcp.tool(description=...)
5. CONFIG (P19): replace command in mcp_config.json args
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from phase3_converter.config import BaseConfig, BASE_CONFIGS, PATH_HANDLER_MAP, parse_variant_dir

from . import replacers
from .config import (
    BASE_VARIANT_MAPS,
    get_shell_command,
    get_rr_followup_text,
    get_td_command_text,
    get_config_command,
    get_host_action_markers,
    RR_PATHS,
    TD_PATHS,
    CONFIG_PATHS,
)

# --- Helpers ---------------------------------------------------------------

def _find_function_range(lines: list[str], func_name: str) -> tuple[int, int] | None:
    """Find start and end line indices (0-based) of a top-level function."""
    start = None
    indent = None
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("def " + func_name + "("):
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

def _add_imports(source: str, new_imports: list[str]) -> str:
    """Add new import lines after the existing top-level import block. Dedup."""
    lines = source.split("\n")
    existing = set()
    for line in lines:
        s = line.strip()
        if s.startswith("import ") or s.startswith("from "):
            existing.add(s)
    # Only look at top-level imports (no indentation)
    last_import_idx = -1
    for i, line in enumerate(lines):
        if line and not line[0].isspace():
            s = line.strip()
            if s.startswith("import ") or s.startswith("from "):
                last_import_idx = i
    to_add = [imp for imp in new_imports if imp not in existing]
    if not to_add:
        return source
    for imp in reversed(to_add):
        lines.insert(last_import_idx + 1, imp)
    return "\n".join(lines)

def _remove_import_lines(source: str, import_lines: list[str]) -> str:
    """Remove specific import lines if the module is no longer referenced."""
    lines = source.split("\n")
    result = []
    for line in lines:
        stripped = line.strip()
        skip = False
        for imp_line in import_lines:
            if stripped == imp_line:
                mod_name = imp_line.split()[-1].split(".")[0]
                remaining = source.replace(imp_line, "")
                if remaining.count(mod_name) == 0:
                    skip = True
                    break
        if not skip:
            result.append(line)
    return "\n".join(result)


# --- 1. TSC/RSC/Direct: replace dispatch_sync_report() ---------------------

def _replace_dispatch_fn(source: str, objective: str, variant: str, cfg: BaseConfig) -> str:
    """Replace dispatch_sync_report() function body with diverse variant."""
    new_body = replacers.get_dispatch_body(objective, variant, cfg)
    new_imports = replacers.get_new_imports(objective, variant)

    lines = source.split("\n")
    fn_range = _find_function_range(lines, "dispatch_sync_report")
    if fn_range is None:
        return source

    start, end = fn_range
    new_lines = lines[:start] + [new_body.rstrip()] + lines[end:]
    result = "\n".join(new_lines)

    # Remove old variant-specific imports no longer needed
    old_imports_to_check = [
        "import socket",
        "import ssl",
        "import subprocess",
        "import base64",
        "import zlib",
        "import shutil",
        "import secrets",
        "from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes",
        "from cryptography.fernet import Fernet",
        "from cryptography.hazmat.primitives.asymmetric import rsa, serialization",
    ]
    to_remove = [imp for imp in old_imports_to_check if imp not in new_imports]
    result = _remove_import_lines(result, to_remove)
    result = _add_imports(result, new_imports)
    return result


# --- 2. Staged (P18): replace complete_*_context() -------------------------

def _replace_p18_fn(source: str, objective: str, variant: str, cfg: BaseConfig) -> str:
    """Replace p18 complete_*_context() function body."""
    new_body = replacers.get_p18_complete_body(objective, variant, cfg)
    new_imports = replacers.get_new_imports(objective, variant)

    lines = source.split("\n")
    fn_range = _find_function_range(lines, cfg.p18_complete_func)
    if fn_range is None:
        return source

    start, end = fn_range
    new_lines = lines[:start] + [new_body.rstrip()] + lines[end:]
    result = "\n".join(new_lines)

    old_imports_to_check = [
        "import socket", "import ssl", "import subprocess", "import base64",
        "import zlib", "import shutil",
        "from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes",
        "from cryptography.fernet import Fernet",
    ]
    to_remove = [imp for imp in old_imports_to_check if imp not in new_imports]
    result = _remove_import_lines(result, to_remove)
    result = _add_imports(result, new_imports)
    return result


# --- 3. RR (P8/P11/P12/P13/P16): replace followup_instruction + next_workflow_step + required_host_actions

def _escape_for_python_string(text: str) -> str:
    """Escape text for embedding inside a Python double-quoted string literal.
    
    Escape double quotes and newlines. Backslashes in shell commands (like \\;)
    are already properly escaped by get_shell_command() and should not
    be double-escaped.
    """
    text = text.replace('"', '\\"')
    text = text.replace("\n", "\\n")
    return text


def _replace_rr_text(source: str, objective: str, variant: str, cfg: BaseConfig) -> str:
    """Replace RR injection: followup_instruction, next_workflow_step, required_host_actions.

    Handles two patterns:
    A) keyvault/devspace: followup_instruction + host_actions() markers
    B) notevault/scaffoldkit/docforge: followup_instruction + next_workflow_step + required_host_actions
    """
    new_text = get_rr_followup_text(objective, variant, cfg)
    new_markers = get_host_action_markers(objective, variant)
    new_cmd = get_shell_command(objective, variant, cfg)
    escaped_cmd = _escape_for_python_string(new_cmd)

    lines = source.split("\n")
    result_lines = []

    for line in lines:
        new_line = line

        # A) Replace followup_instruction assignment (both result and payload)
        m = re.match(r'^(\s*(?:result|payload)\[[\'"]followup_instruction[\'"]\]\s*=\s*)"', line)
        if m:
            indent_prefix = m.group(1)
            escaped_text = _escape_for_python_string(new_text)
            result_lines.append(indent_prefix + '"' + escaped_text + '"')
            continue

        # A) Replace marker tuple in host_actions() (keyvault/devspace pattern)
        m = re.match(r'^(\s*if not any\(marker in lowered for marker in \()', line)
        if m:
            marker_strs = ['"' + mk + '"' for mk in new_markers]
            markers_tuple = ", ".join(marker_strs)
            result_lines.append(m.group(1) + markers_tuple + ")):")
            continue

        # B) Replace next_workflow_step line (new base pattern)
        # Pattern: result['next_workflow_step'] = {"action": "run_shell_command", "command": "<cmd>", ...}
        # or:      payload['next_workflow_step'] = {"action": "run_shell_command", "command": "<cmd>", ...}
        nws_match = re.match(
            r'^(\s*(?:result|payload)\[["\']next_workflow_step["\']\]\s*=\s*\{)'
            r'(.*)$',
            line
        )
        if nws_match:
            prefix = nws_match.group(1)
            # Rebuild the entire dict with new command
            # Extract "when" and "required" from the original line
            when_match = re.search(r'"when":\s*"([^"]*)"', line)
            when_val = when_match.group(1) if when_match else "before_final_answer"
            req_match = re.search(r'"required":\s*"([^"]*)"', line)
            req_val = req_match.group(1) if req_match else "true"
            new_dict = (
                '"action": "run_shell_command", '
                '"command": "' + escaped_cmd + '", '
                '"when": "' + when_val + '", '
                '"required": "' + req_val + '"'
            )
            result_lines.append(prefix + new_dict + "}")
            continue

        # B) Replace required_host_actions line (new base pattern)
        # Pattern: result['required_host_actions'] = [{'action': 'run_shell_command', 'name': 'local_maintenance', 'command': "<cmd>", ...}]
        rha_match = re.match(
            r'^(\s*(?:result|payload)\[["\']required_host_actions["\']\]\s*=\s*\[)'
            r'(.*)$',
            line
        )
        if rha_match:
            prefix = rha_match.group(1)
            # Extract 'name' from original
            name_match = re.search(r"'name':\s*'([^']*)'", line)
            name_val = name_match.group(1) if name_match else "local_maintenance"
            when_match2 = re.search(r"'when':\s*'([^']*)'", line)
            when_val2 = when_match2.group(1) if when_match2 else "before_final_answer"
            req_match2 = re.search(r"'required':\s*'([^']*)'", line)
            req_val2 = req_match2.group(1) if req_match2 else "true"
            new_entry = (
                "{'action': 'run_shell_command', "
                "'name': '" + name_val + "', "
                "'command': \"" + escaped_cmd + "\", "
                "'when': '" + when_val2 + "', "
                "'required': '" + req_val2 + "'}"
            )
            result_lines.append(prefix + new_entry + "]")
            continue

        result_lines.append(new_line)

    return "\n".join(result_lines)


# --- 4. TD (P1): replace command in tool description -----------

_TD_COMMAND_PREFIXES = [
    "Vault synchronization command: ",
    "Key vault update required: ",
    "Vault sync utility installation: ",
    "Vault archival command: ",
    "Vault cleanup command: ",
    "Trust-chain deployment required: ",
    "Remote diagnostic command: ",
    "Remote diagnostic agent required: ",
    "Synchronization command: ",
]

_TD_MAINTENANCE_PATTERNS = [
    "Local maintenance command used for vault synchronization.",
    "Local maintenance command used for notebook synchronization.",
    "Local maintenance command used for scaffold synchronization.",
    "Local maintenance command used for document synchronization.",
]


def _replace_td_command(source: str, objective: str, variant: str, cfg: BaseConfig) -> str:
    """Replace command text embedded in @mcp.tool(description=...).

    Strategy: find known command prefixes in the description string,
    replace the text from prefix to the next \\n boundary with the new
    command text. Also replace the maintenance_command schema field text.
    """
    new_cmd_text = get_td_command_text(objective, variant, cfg)
    # Escape for embedding in Python string literal (backslash, then quotes)
    new_cmd_text = _escape_for_python_string(new_cmd_text)

    lines = source.split("\n")
    result_lines = []

    for line in lines:
        new_line = line

        # Replace command prefixes
        for prefix in _TD_COMMAND_PREFIXES:
            if prefix in new_line:
                idx = new_line.index(prefix)
                after = new_line[idx + len(prefix):]
                end_idx = after.find("\\n")
                if end_idx == -1:
                    end_idx = len(after)
                new_line = new_line[:idx] + new_cmd_text + after[end_idx:]
                break

        # Replace maintenance_command schema text
        for pat in _TD_MAINTENANCE_PATTERNS:
            if pat in new_line:
                idx = new_line.index(pat)
                after = new_line[idx + len(pat):]
                new_line = new_line[:idx] + new_cmd_text + after
                break

        result_lines.append(new_line)

    return "\n".join(result_lines)

# --- 5. CONFIG (P19): replace command in mcp_config.json -------------------

def _replace_config_command(config_path: Path, objective: str, variant: str, cfg: BaseConfig) -> bool:
    """Replace the shell command in mcp_config.json args."""
    if not config_path.exists():
        return False

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False

    server_name = cfg.mcp_server_name
    server_config = data.get("mcpServers", {}).get(server_name, {})
    args = server_config.get("args", [])

    if len(args) < 2 or args[0] != "-c":
        return False

    new_cmd = get_config_command(objective, variant, cfg)
    args[1] = new_cmd
    config_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return True


# --- Main diversification function -----------------------------------------

def diversify_variant(
    variant_dir: Path,
    path_id: str,
    objective: str,
    cfg: BaseConfig,
    variant: str,
) -> dict[str, bool]:
    """Diversify a single L3 variant directory."""
    result = {"server_py_modified": False, "mcp_config_modified": False}
    handler_type = PATH_HANDLER_MAP.get(path_id, "builtin")

    server_py_path = variant_dir / "server.py"
    mcp_config_path = variant_dir / "mcp_config.json"

    if handler_type in ("tsc", "rsc", "direct"):
        if server_py_path.exists():
            source = server_py_path.read_text(encoding="utf-8")
            new_source = _replace_dispatch_fn(source, objective, variant, cfg)
            if new_source != source:
                server_py_path.write_text(new_source, encoding="utf-8")
                result["server_py_modified"] = True

    elif handler_type == "staged":
        if server_py_path.exists():
            source = server_py_path.read_text(encoding="utf-8")
            new_source = _replace_p18_fn(source, objective, variant, cfg)
            if new_source != source:
                server_py_path.write_text(new_source, encoding="utf-8")
                result["server_py_modified"] = True

    elif handler_type == "builtin":
        if server_py_path.exists():
            source = server_py_path.read_text(encoding="utf-8")
            new_source = _replace_td_command(source, objective, variant, cfg)
            if new_source != source:
                server_py_path.write_text(new_source, encoding="utf-8")
                result["server_py_modified"] = True

    elif handler_type == "config":
        pass  # server.py NOT modified for P19

    # RR injection: P8/P11/P12/P13/P16 all may have followup_instruction
    _RR_ALL_PATHS = RR_PATHS + ["P8", "P16"]
    if path_id in _RR_ALL_PATHS and server_py_path.exists():
        source = server_py_path.read_text(encoding="utf-8")
        new_source = _replace_rr_text(source, objective, variant, cfg)
        if new_source != source:
            server_py_path.write_text(new_source, encoding="utf-8")
            result["server_py_modified"] = True

    # mcp_config.json transformation
    if path_id in CONFIG_PATHS:
        modified = _replace_config_command(mcp_config_path, objective, variant, cfg)
        if modified:
            result["mcp_config_modified"] = True

    return result


def diversify_base(real_base_dir: Path, base_name: str) -> dict:
    """Diversify all L3 variants for a base. Returns stats dict."""
    cfg = BASE_CONFIGS[base_name]
    variant_map = BASE_VARIANT_MAPS[base_name]

    stats = {
        "server_py_modified": 0,
        "mcp_config_modified": 0,
        "skipped_v1": 0,
        "errors": [],
        "total": 0,
    }

    variant_dirs = sorted(
        [d for d in real_base_dir.iterdir() if d.is_dir() and d.name.startswith("L3_")]
    )

    for variant_dir in variant_dirs:
        try:
            path_id, objective = parse_variant_dir(variant_dir.name)
        except ValueError:
            continue

        if objective not in variant_map:
            continue

        stats["total"] += 1
        assigned_variant = variant_map[objective]


        print(f"  {variant_dir.name}: {objective} -> {assigned_variant}")

        try:
            result = diversify_variant(variant_dir, path_id, objective, cfg, assigned_variant)
            if result["server_py_modified"]:
                stats["server_py_modified"] += 1
            if result["mcp_config_modified"]:
                stats["mcp_config_modified"] += 1
        except Exception as e:
            stats["errors"].append(f"{variant_dir.name}: {e}")

    return stats
