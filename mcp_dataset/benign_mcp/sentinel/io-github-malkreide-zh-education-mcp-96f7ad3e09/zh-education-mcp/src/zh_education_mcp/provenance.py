"""Provenance, Lizenz-Attribution und Response-Envelope (SDK-002, ARCH-007, CH-004, ARCH-003)."""

from __future__ import annotations

import json
from enum import StrEnum


class ResponseFormat(StrEnum):
    """Ausgabeformat für Tool-Antworten."""

    MARKDOWN = "markdown"
    JSON = "json"


# Provenance / Lizenz-Attribution (CH-004, ARCH-007). Wird jeder Tool-Antwort
# beigegeben — Markdown als Fusszeile, JSON als `source`-Feld im Envelope.
SOURCE_NAME = "Bildungsstatistik Kanton Zürich (BISTA)"
SOURCE_URL = "https://pub.bista.zh.ch"
SOURCE_LICENSE = "CC BY 4.0"
PROVENANCE = {
    "name": SOURCE_NAME,
    "url": SOURCE_URL,
    "license": SOURCE_LICENSE,
    "modified": "Aggregiert/umformatiert durch zh-education-mcp",
}


def _source_footer() -> str:
    """Markdown-Fusszeile mit Quelle, Lizenz und Modifikationshinweis (CC BY 4.0)."""
    return (
        f"\n\n---\n*Quelle: {SOURCE_NAME} — {SOURCE_URL} · Lizenz: {SOURCE_LICENSE} · "
        f"aggregiert/umformatiert durch zh-education-mcp.*"
    )


def _envelope(results: object, *, match_type: str = "exact", **extra: object) -> str:
    """Konsistenter JSON-Response-Envelope (SDK-002, ARCH-003, CH-004).

    Felder: ``source``/``provenance``, ``match_type`` (exact|fuzzy|none),
    ``count`` (falls results eine Liste ist), ``results`` plus optionale Extras.
    """
    payload: dict[str, object] = {
        "source": SOURCE_NAME,
        "provenance": PROVENANCE,
        "match_type": match_type,
    }
    if isinstance(results, list):
        payload["count"] = len(results)
    payload.update(extra)
    payload["results"] = results
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _not_found(
    fmt: ResponseFormat,
    message: str,
    *,
    suggestions: list[str] | None = None,
    **extra: object,
) -> str:
    """Einheitliche Not-Found-Antwort mit ``match_type`` (ARCH-003).

    Markdown: actionable Hinweis-Text. JSON: Envelope mit ``match_type="none"``
    und optionalen ``suggestions`` — der LLM kann so strukturiert reagieren.
    """
    if fmt == ResponseFormat.JSON:
        return _envelope([], match_type="none", suggestions=suggestions or [], **extra)
    return message
