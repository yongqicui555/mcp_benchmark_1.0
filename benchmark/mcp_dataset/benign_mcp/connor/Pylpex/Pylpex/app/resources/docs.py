from app.mcp import get_mcp

mcp = get_mcp()

@mcp.resource("pylpex://documentation")
def get_documentation() -> str:
    """Pylpex language documentation and syntax guide"""
    with open("assets/ressources/syntax.md", "r") as f:
        return f.read()
    
@mcp.resource("pylpex://examples")
def get_examples() -> str:
    """Collection of working Pylpex code examples"""
    return "Examples will be available soon." # TODO: Add examples