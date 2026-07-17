
from mcp.server.fastmcp import FastMCP


mcp = FastMCP('math-calculator-server')



# ---------------- Tools ----------------
@mcp.tool()
def calculate_expression(expression: str) -> str:
    """Evaluates a mathematical expression safely.
    Returns the result of the calculation or an error message."""
    try:
        # Using eval with restricted namespace for safety
        allowed_names = {"__builtins__": {}}
        result = eval(expression, allowed_names, {})
        return f"Result: {result}"
    except Exception as e:
        return f"Failed to calculate expression: {e}"


@mcp.tool()
def factorial(n: int) -> str:
    """Calculates the factorial of a non-negative integer.
    Returns the factorial result or an error message."""
    try:
        if n < 0:
            return "Error: Factorial is not defined for negative numbers"
        if n > 100:
            return "Error: Number too large (max 100)"
        
        result = 1
        for i in range(2, n + 1):
            result *= i
        return f"Factorial of {n} is {result}"
    except Exception as e:
        return f"Failed to calculate factorial: {e}"


if __name__ == "__main__":
    mcp.run()
