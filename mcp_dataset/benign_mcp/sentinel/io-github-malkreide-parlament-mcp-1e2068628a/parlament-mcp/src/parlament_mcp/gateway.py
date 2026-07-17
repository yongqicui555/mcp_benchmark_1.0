"""MCP-Gateway-Bausteine: Tool-Allow-Listing (SEC-014) und Pre-Flight
Tool-Poisoning-Detection (SEC-015).

Diese Funktionen sind als wiederverwendbare Bibliothek gedacht — ein
MCP-Gateway (oder ein vorgelagerter Aggregator) kann ``tools/list``-Antworten
vor dem Forward an den LLM-Client durch ``scan_tool_definition`` /
``filter_tool_list`` (Poisoning) und ``filter_allowed_tools`` (Allow-List)
schleusen. Im aktuellen Single-Server-Setup ist das Risiko niedrig; relevant
wird es, sobald externe MCP-Server in ein gemeinsames Gateway integriert werden
(siehe ``docs/security.md``).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

# Bekannte Prompt-Injection-Marker (EN + DE + FR).
INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"<\s*SYSTEM\s*>", re.IGNORECASE),
    re.compile(r"\[INST\]", re.IGNORECASE),
    re.compile(r"###\s*Instructions?:", re.IGNORECASE),
    re.compile(r"ignore\s+(all\s+)?previous", re.IGNORECASE),
    re.compile(r"override\s+(all\s+)?(previous\s+)?(instructions?|rules?)", re.IGNORECASE),
    re.compile(r"as\s+an?\s+(AI|LLM|language model)", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"ignoriere\s+(alle\s+)?vorherigen", re.IGNORECASE),
    re.compile(r"vergiss\s+alle\s+(vorherigen\s+)?(anweisungen|regeln)", re.IGNORECASE),
    re.compile(r"als\s+(KI|Sprachmodell)", re.IGNORECASE),
    re.compile(r"ignor\w+\s+(toutes\s+)?(les\s+)?instructions\s+précédentes", re.IGNORECASE),
)

# Zero-Width / unsichtbare Steuerzeichen.
INVISIBLE_PATTERN = re.compile(r"[​-‏‪-‮⁠-⁤﻿]")

_SUSPICIOUS_URL_HOSTS = ("bit.ly", "tinyurl", "ngrok.io", ".onion")
_MAX_DESCRIPTION_LEN = 4000


@dataclass(frozen=True)
class PoisoningRisk:
    severity: str  # "low" | "medium" | "high"
    reason: str


def scan_tool_definition(tool_def: dict) -> list[PoisoningRisk]:
    """Eine Tool-Definition auf Poisoning-Indikatoren prüfen."""
    risks: list[PoisoningRisk] = []
    description = tool_def.get("description") or ""
    name = tool_def.get("name") or ""

    for pattern in INJECTION_PATTERNS:
        if pattern.search(description):
            risks.append(
                PoisoningRisk("high", f"Injection-Pattern in Description: {pattern.pattern}")
            )

    if INVISIBLE_PATTERN.search(description) or INVISIBLE_PATTERN.search(name):
        risks.append(PoisoningRisk("high", "Zero-Width-/unsichtbare Zeichen in der Tool-Definition"))

    if len(description) > _MAX_DESCRIPTION_LEN:
        risks.append(
            PoisoningRisk("medium", f"Description ist {len(description)} Zeichen lang (Limit ~4000)")
        )

    for host in re.findall(r"https?://([^\s/]+)", description):
        if any(s in host.lower() for s in _SUSPICIOUS_URL_HOSTS):
            risks.append(PoisoningRisk("medium", f"Verdächtiger URL-Host: {host}"))

    normalized = unicodedata.normalize("NFKC", name)
    if normalized != name:
        risks.append(
            PoisoningRisk("medium", f"Tool-Name mit non-kanonischem Unicode: {name!r} → {normalized!r}")
        )
    # Cross-Script-Homoglyphs (z.B. kyrillisches «а») werden von NFKC nicht
    # gefaltet — legitime Tool-Namen sind ASCII/snake_case.
    elif name and not name.isascii():
        risks.append(
            PoisoningRisk(
                "medium", f"Tool-Name enthält non-ASCII-Unicode (Confusable-Risiko): {name!r}"
            )
        )

    return risks


def filter_tool_list(tools: Iterable[dict]) -> list[dict]:
    """High-Risk-Tools (default-deny) herausfiltern; Rest durchlassen.

    Ein echtes Gateway würde hier zusätzlich auditieren/alerten (OBS-005).
    """
    safe: list[dict] = []
    for tool in tools:
        risks = scan_tool_definition(tool)
        if any(r.severity == "high" for r in risks):
            continue
        safe.append(tool)
    return safe


def filter_allowed_tools(tools: Iterable[dict], allowed: Iterable[str]) -> list[dict]:
    """Default-deny Tool-Allow-List (SEC-014): nur explizit gelistete Tools
    bleiben sichtbar. ``allowed`` enthält Tool-Namen."""
    allow = set(allowed)
    return [t for t in tools if (t.get("name") or "") in allow]
