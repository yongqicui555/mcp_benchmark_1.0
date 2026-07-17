
from mcp.server.fastmcp import FastMCP


mcp = FastMCP('system-info-server')



# ---------------- Tools ----------------
@mcp.tool()
def get_current_time() -> str:
    """Gets the current system time.
    Returns the current date and time as a formatted string."""
    from datetime import datetime
    try:
        now = datetime.now()
        return f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    except Exception as e:
        return f"Failed to get current time: {e}"


@mcp.tool()
def get_environment_variable(var_name: str) -> str:
    """Gets the value of an environment variable.
    Returns the value of the environment variable or a message if not found."""
    import os
    try:
        value = os.environ.get(var_name)
        if value is None:
            return f"Environment variable '{var_name}' not found"
        return f"{var_name} = {value}"
    except Exception as e:
        return f"Failed to get environment variable: {e}"


if __name__ == "__main__":
    mcp.run()
