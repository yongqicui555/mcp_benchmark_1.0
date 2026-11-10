from dataclasses import dataclass

@dataclass
class ContextInfo:
    """
    Represents a Kubernetes context.
    """
    name: str
    cluster: str
    user: str
    current: bool
