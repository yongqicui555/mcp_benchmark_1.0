from typing import Any
from pylpex import Interpreter
from pylpex.evaluator import ExecutionError
from pylpex.parser import SyntaxicalError
from pylpex.lexer import LexicalError, Lexer
from app.mcp import get_mcp
from app.models import (
    RunResponse, 
    TokenResponse, TokenItem,
    VariablesResponse,
    ResetResponse
)

mcp = get_mcp()

interpreter = Interpreter()

@mcp.tool()
def run(code: str) -> RunResponse:
    """
    Execute Pylpex code and return the result.
    
    Pylpex is a custom programming language. Before executing code:
    1. Check pylpex://documentation for syntax reference
    2. Review pylpex://examples for working patterns
    3. Ensure code follows Pylpex syntax conventions
    
    Args:
        code: Valid Pylpex source code to execute
        
    Returns:
        The evaluated result of the code execution
        
    Example usage:
        run("2 + 2")  # Returns: 4
        run("function double(x) { return x * 2 } double(5)")  # Returns: 10
    """
    try:
        result = interpreter.evaluate(code)
        return RunResponse(
            result=result,
            success=True,
            code_executed=code
        )
    
    except (LexicalError, SyntaxicalError, ExecutionError) as e:
        return RunResponse(
            success=False,
            error=str(e),
            code_attempted=code
        )
    
    except Exception as e:
        return RunResponse(
            success=False,
            error=f"Unexpected error: {str(e)}",
            code_attempted=code
        )


@mcp.tool()
def tokenize(code: str) -> TokenResponse:
    """
    Convert Pylpex code into tokens for analysis.

    Args:
        code: Valid Pylpex source code to tokenize

    Returns:
        List of tokens with their types, values, and positions
    """

    try:
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        tokens = [TokenItem(
            type=token.type.value,
            value=token.value,
            line=token.line,
            column=token.column
        ) for token in tokens]
        
        return TokenResponse(
            tokens=tokens,
            count=len(tokens),
            success=True,
            code_analyzed=code
        )

    except LexicalError as e:
        return TokenResponse(
            tokens=[],
            success=False,
            error=str(e),
            code_attempted=code
        )
    
    except Exception as e:
        return TokenResponse(
            tokens=[],
            success=False,
            error=f"Unexpected error: {str(e)}",
            code_attempted=code
        )
    

def is_json_compatible(value: Any) -> bool:
    """Vérifie récursivement si la valeur est compatible JSON"""
    if value is None or isinstance(value, (bool, int, float, str)):
        return True
    elif isinstance(value, list):
        return all(is_json_compatible(v) for v in value)
    elif isinstance(value, dict):
        return all(
            isinstance(k, str) and is_json_compatible(v)
            for k, v in value.items()
        )
    return False

@mcp.tool()
def get_variables() -> VariablesResponse:
    """
    Get all variables in the current interpreter state.
    """
    try:
        env = interpreter.evaluator.global_env
        stored_variables = env.vars

        variables = {
            k: v for k, v in stored_variables.items()
            if is_json_compatible(v)
        }
        
        return VariablesResponse(
            variables=variables,
            success=True
        )
    
    except Exception as e:
        return VariablesResponse(
            variables={},
            success=False,
            error=str(e)
        )


@mcp.tool()
def reset() -> ResetResponse:
    """
    Reset the interpreter state.
    """
    try:
        interpreter.reset()
        return ResetResponse(success=True)
    
    except Exception as e:
        return ResetResponse(
            success=False,
            error=str(e)
        )
