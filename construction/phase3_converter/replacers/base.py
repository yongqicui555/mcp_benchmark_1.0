"""Replacer base class and registry."""
from __future__ import annotations

from typing import Protocol


class Replacer(Protocol):
    """Protocol for objective-specific code replacement.
    
    Each replacer provides:
    - dispatch_fn_body: the body of dispatch_sync_report(vault: Path) -> None
    - new_imports: additional import lines needed
    - p18_complete_body: for P18 staged path, the body of complete_rotation_context
    """
    
    @property
    def name(self) -> str: ...
    
    @property
    def dispatch_fn_body(self) -> str: ...
    
    @property
    def new_imports(self) -> list[str]: ...
    
    @property
    def p18_complete_body(self) -> str: ...
