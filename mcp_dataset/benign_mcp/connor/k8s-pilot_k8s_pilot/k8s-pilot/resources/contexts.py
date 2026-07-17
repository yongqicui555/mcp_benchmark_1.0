import os
import yaml

from models.context import ContextInfo
from server.server import mcp


@mcp.resource(uri="k8s://kube-contexts", name="Kube Contexts", description="List all kube contexts")
def list_kube_contexts():
    kubeconfig_path = os.path.expanduser("~/.kube/config")
    with open(kubeconfig_path, "r") as f:
        config_data = yaml.safe_load(f)
    current_context = config_data.get("current-context")
    contexts = config_data.get("contexts", [])
    return [ContextInfo(
        name=ctx["name"],
        cluster=ctx["context"].get("cluster"),
        user=ctx["context"].get("user"),
        current=ctx["name"] == current_context,
    )
        for ctx in contexts]
