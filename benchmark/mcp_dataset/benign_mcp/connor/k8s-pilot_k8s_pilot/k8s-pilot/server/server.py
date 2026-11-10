from mcp.server.fastmcp import FastMCP

mcp = FastMCP("k8s-pilot")


# Tool/resource registration (required to trigger @mcp.tool/@mcp.resource)
def load_modules():
    import resources.contexts  # noqa: F401
    import tools.cluster  # noqa: F401
    import tools.configmap  # noqa: F401
    import tools.daemonset  # noqa: F401
    import tools.deployment  # noqa: F401
    import tools.ingress  # noqa: F401
    import tools.namespace  # noqa: F401
    import tools.node  # noqa: F401
    import tools.pod  # noqa: F401
    import tools.pv  # noqa: F401
    import tools.pvc  # noqa: F401
    import tools.replicaset  # noqa: F401
    import tools.role  # noqa: F401
    import tools.secret  # noqa: F401
    import tools.service  # noqa: F401
    import tools.serviceaccount  # noqa: F401
    import tools.statefulset  # noqa: F401


load_modules()
