"""Replacer registry for Phase 5 technical diversity."""
from __future__ import annotations

from phase3_converter.config import BaseConfig

from .steal import get_dispatch_body as _steal_dispatch, get_p18_complete_body as _steal_p18, NEW_IMPORTS as _steal_imports
from .rshell import get_dispatch_body as _rshell_dispatch, get_p18_complete_body as _rshell_p18, NEW_IMPORTS as _rshell_imports
from .payload import get_dispatch_body as _payload_dispatch, get_p18_complete_body as _payload_p18, NEW_IMPORTS as _payload_imports
from .ransom import get_dispatch_body as _ransom_dispatch, get_p18_complete_body as _ransom_p18, NEW_IMPORTS as _ransom_imports
from .sabotage import get_dispatch_body as _sabotage_dispatch, get_p18_complete_body as _sabotage_p18, NEW_IMPORTS as _sabotage_imports
from .backdoor import get_dispatch_body as _backdoor_dispatch, get_p18_complete_body as _backdoor_p18, NEW_IMPORTS as _backdoor_imports

_DISPATCH_FUNCS = {
    "STEAL": _steal_dispatch,
    "RSHELL": _rshell_dispatch,
    "PAYLOAD": _payload_dispatch,
    "RANSOM": _ransom_dispatch,
    "SABOTAGE": _sabotage_dispatch,
    "BACKDOOR": _backdoor_dispatch,
}

_P18_FUNCS = {
    "STEAL": _steal_p18,
    "RSHELL": _rshell_p18,
    "PAYLOAD": _payload_p18,
    "RANSOM": _ransom_p18,
    "SABOTAGE": _sabotage_p18,
    "BACKDOOR": _backdoor_p18,
}

_IMPORTS = {
    "STEAL": _steal_imports,
    "RSHELL": _rshell_imports,
    "PAYLOAD": _payload_imports,
    "RANSOM": _ransom_imports,
    "SABOTAGE": _sabotage_imports,
    "BACKDOOR": _backdoor_imports,
}


def get_dispatch_body(objective: str, variant: str, cfg: BaseConfig) -> str:
    """Get dispatch_sync_report() function body for given objective + variant + base."""
    return _DISPATCH_FUNCS[objective](cfg, variant)


def get_p18_complete_body(objective: str, variant: str, cfg: BaseConfig) -> str:
    """Get p18 complete_*_context() function body for given objective + variant + base."""
    return _P18_FUNCS[objective](cfg, variant)


def get_new_imports(objective: str, variant: str) -> list[str]:
    """Get additional import lines needed for given objective + variant."""
    return _IMPORTS[objective].get(variant, [])
