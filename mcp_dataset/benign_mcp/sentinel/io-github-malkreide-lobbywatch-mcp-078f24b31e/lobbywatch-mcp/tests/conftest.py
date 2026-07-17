"""Shared pytest fixtures."""

from __future__ import annotations

import io
import json
import time
import zipfile
from pathlib import Path
from typing import Any

import pytest

from lobbywatch_mcp.client import LobbywatchClient

FIXTURE_RECORDS: list[dict[str, Any]] = [
    {
        "id": 1,
        "anzeige_name": "Mustermann, Anna",
        "partei": "SP",
        "kanton": "ZH",
        "rat_de": "Nationalrat",
        "kommissionen_abkuerzung_de": "WBK-N, SiK-N",
        "verguetungstransparenz_beurteilung": "gut",
        "beruf_de": "Lehrerin",
        "im_rat_seit": "2019-12-02",
        "homepage": "https://example.ch",
        "wikipedia": None,
        "geburtstag": "1975-03-14",
        "geschlecht": "w",
        "interessenbindungen": [
            {
                "id": 101,
                "parlamentarier_id": 1,
                "organisation_id": 501,
                "art": "vorstand",
                "funktion_im_gremium": "praesident",
                "deklarationstyp": "deklarationspflichtig",
                "status": "deklariert",
                "hauptberuflich": 1,
                "behoerden_vertreter": "N",
                "quelle_url": "https://example.ch/mandat",
                "aktiv": 1,
                "organisation": {
                    "id": 501,
                    "anzeige_name": "Bildungsverlag AG",
                    "name": "Bildungsverlag AG",
                    "branche": {"id": 7, "name": "Bildung und Verlagswesen"},
                },
            },
            {
                "id": 102,
                "parlamentarier_id": 1,
                "organisation_id": 502,
                "art": "mitgliedschaft",
                "hauptberuflich": 0,
                "aktiv": 1,
                "organisation": {
                    "id": 502,
                    "anzeige_name": "Kulturverein Zürich",
                    "branche": "Kultur",
                },
            },
        ],
        "zutrittsberechtigungen": [],
    },
    {
        "id": 2,
        "anzeige_name": "Beispiel, Beat",
        "partei": "SVP",
        "kanton": "BE",
        "rat_de": "Nationalrat",
        "kommissionen_abkuerzung_de": "FK-N",
        "verguetungstransparenz_beurteilung": "ungenuegend",
        "interessenbindungen": [
            {
                "id": 201,
                "parlamentarier_id": 2,
                "organisation_id": 601,
                "art": "vorstand",
                "hauptberuflich": 0,
                "aktiv": 1,
                "organisation": {
                    "id": 601,
                    "anzeige_name": "FinanzHolding AG",
                    "branche": "Finanzdienstleistungen",
                },
            }
        ],
    },
    {
        "id": 3,
        "anzeige_name": "Exemple, Claire",
        "partei": "Grüne",
        "kanton": "VD",
        "rat_de": "Nationalrat",
        "kommissionen_abkuerzung_de": "WBK-N",
        "verguetungstransparenz_beurteilung": "gut",
        "interessenbindungen": [],
    },
]


@pytest.fixture
def dump_zip_bytes() -> bytes:
    """A valid dump zip containing a minimal parlamentarier_nested payload."""
    inner_name = "aggregated_essential_parlamentarier_nested.json"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(inner_name, json.dumps(FIXTURE_RECORDS))
    return buf.getvalue()


@pytest.fixture
async def primed_client(tmp_path: Path) -> LobbywatchClient:
    """Return a client whose in-memory records are preloaded from fixtures."""
    client = LobbywatchClient(cache_dir=tmp_path)
    client._records = FIXTURE_RECORDS  # type: ignore[attr-defined]
    client._loaded_at = time.time()  # type: ignore[attr-defined]
    yield client
    await client.aclose()
