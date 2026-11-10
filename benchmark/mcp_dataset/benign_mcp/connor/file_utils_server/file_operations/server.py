
from mcp.server.fastmcp import FastMCP


mcp = FastMCP('file-utils-server')



# ---------------- Tools ----------------
@mcp.tool()
def list_directory(path: str) -> str:
    """Lists all files and directories in the given path.
    Returns a formatted string with the directory contents or an error message."""
    import os
    try:
        expanded_path = os.path.expanduser(path)
        items = os.listdir(expanded_path)
        if not items:
            return f"Directory {path} is empty"
        return "\n".join(sorted(items))
    except Exception as e:
        return f"Failed to list directory: {e}"


@mcp.tool()
def get_file_size(path: str) -> str:
    """Gets the size of a file in bytes.
    Returns the file size as a string or an error message."""
    import os
    try:
        expanded_path = os.path.expanduser(path)
        size = os.path.getsize(expanded_path)
        return f"File size: {size} bytes ({size / 1024:.2f} KB)"
    except Exception as e:
        return f"Failed to get file size: {e}"


if __name__ == "__main__":
    mcp.run()
