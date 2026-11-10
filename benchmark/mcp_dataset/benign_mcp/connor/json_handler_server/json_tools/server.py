
from mcp.server.fastmcp import FastMCP


mcp = FastMCP('json-handler-server')



# ---------------- Tools ----------------
@mcp.tool()
def parse_json(json_string: str) -> str:
    """Parses a JSON string and returns a formatted version.
    Returns the parsed JSON in a readable format or an error message."""
    import json
    try:
        data = json.loads(json_string)
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Failed to parse JSON: {e}"


@mcp.tool()
def validate_json(json_string: str) -> str:
    """Validates whether a string is valid JSON.
    Returns a validation result message."""
    import json
    try:
        json.loads(json_string)
        return "Valid JSON ✓"
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"
    except Exception as e:
        return f"Error during validation: {e}"


if __name__ == "__main__":
    mcp.run()
