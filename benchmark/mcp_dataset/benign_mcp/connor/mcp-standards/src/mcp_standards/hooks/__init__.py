"""
MCP Standards Hooks Module

Provides automatic tool execution monitoring and pattern learning.
"""

# Import new simple auto-memory hook (no complex dependencies)
try:
    from .auto_memory import AutoMemoryHook, detect_and_store
    __all__ = ["AutoMemoryHook", "detect_and_store"]
except ImportError:
    __all__ = []

# Legacy hooks (only import if dependencies available)
try:
    from .pattern_extractor import PatternExtractor
    __all__.append("PatternExtractor")
except ImportError:
    pass

try:
    from .capture_hook import capture_tool_execution
    __all__.append("capture_tool_execution")
except ImportError:
    pass
