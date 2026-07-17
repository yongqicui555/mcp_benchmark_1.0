
from typing import Any, List, Dict, Optional
from pydantic import BaseModel, Field, JsonValue

# ==================== Execution ====================

# Interpréteur
class RunResponse(BaseModel):
    """Réponse d'exécution"""
    result: Optional[Any] = None
    success: bool = True
    error: Optional[str] = None
    code_executed: Optional[str] = None
    code_attempted: Optional[str] = None

class VariablesResponse(BaseModel):
    """Réponse de variables"""
    variables: Dict[str, JsonValue]
    success: bool = True
    error: Optional[str] = None

class ResetResponse(BaseModel):
    """Réponse de réinitialisation"""
    success: bool = True
    error: Optional[str] = None

# Lexer
class TokenItem(BaseModel):
    """Représente un jeton lexical Pylpex"""
    type: str
    value: str
    line: int
    column: int

class TokenResponse(BaseModel):
    """Réponse de tokenisation Pylpex"""
    tokens: List[TokenItem]
    count: Optional[int] = None
    success: bool = True
    error: Optional[str] = None
    code_analyzed: Optional[str] = None
    code_attempted: Optional[str] = None

