"""Pydantic-v2-Input-Modelle für die Tools (strikte Validierung — SEC-018)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .provenance import ResponseFormat

_STRICT = ConfigDict(
    str_strip_whitespace=True, validate_assignment=True, extra="forbid", strict=True
)


class ListSchulgemeindensInput(BaseModel):
    """Input für die Auflistung aller Schulgemeinden."""

    model_config = _STRICT

    suchbegriff: str | None = Field(
        default=None,
        max_length=200,
        description="Optionaler Suchbegriff zum Filtern (z. B. 'Zürich', 'Letzi', 'Adliswil')",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, strict=False)


class SchulkreisTrendInput(BaseModel):
    """Input für Schulkreis-Trend-Abfrage."""

    model_config = _STRICT

    schulgemeinde: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Schulgemeinde / Schulkreis (z. B. 'Zürich-Letzi', 'Adliswil', 'Winterthur')",
    )
    letzte_n_jahre: int = Field(
        default=5, ge=1, le=30, description="Anzahl der letzten Jahre (Standard: 5)"
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, strict=False)

    @field_validator("schulgemeinde")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Schulgemeinde darf nicht leer sein.")
        return v


class UebersichtInput(BaseModel):
    """Input für die kantonsweite Übersicht."""

    model_config = _STRICT

    jahr: int | None = Field(
        default=None, description="Bestimmtes Jahr (leer = aktuellstes verfügbares Jahr)"
    )
    stufe: str | None = Field(
        default=None,
        max_length=100,
        description="Schulstufe filtern (z. B. 'Primarstufe', 'Sekundarstufe I')",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, strict=False)


class Sek1ProfilInput(BaseModel):
    """Input für das Sek-I-Profil einer Schulgemeinde."""

    model_config = _STRICT

    schulgemeinde: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Schulgemeinde (z. B. 'Zürich-Letzi', 'Winterthur')",
    )
    jahr: int | None = Field(default=None, description="Bestimmtes Jahr (leer = aktuellstes)")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, strict=False)

    @field_validator("schulgemeinde")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Schulgemeinde darf nicht leer sein.")
        return v


class StaatsangehoerigkeitInput(BaseModel):
    """Input für Staatsangehörigkeitsabfrage."""

    model_config = _STRICT

    schulgemeinde: str = Field(
        ..., min_length=1, max_length=200, description="Schulgemeinde (z. B. 'Zürich-Letzi')"
    )
    top_n: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Anzahl der häufigsten Staatsangehörigkeiten (Standard: 10)",
    )
    jahr: int | None = Field(default=None, description="Bestimmtes Jahr (leer = aktuellstes)")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, strict=False)


class MaturitaetsquoteInput(BaseModel):
    """Input für Maturitätsquoten-Abfrage."""

    model_config = _STRICT

    gemeinde: str | None = Field(
        default=None,
        max_length=200,
        description="Gemeindename filtern (z. B. 'Zürich', 'Winterthur'). Leer = alle.",
    )
    bezirk: str | None = Field(
        default=None, max_length=200, description="Bezirk filtern (z. B. 'Zürich', 'Dietikon')"
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, strict=False)


class WohnortTrendInput(BaseModel):
    """Input für wohnortbasierte Lernenden-Trends."""

    model_config = _STRICT

    gebiet: str | None = Field(
        default=None,
        max_length=200,
        description="Gebietsbezeichnung filtern (z. B. 'Zürich', 'Bezirk Winterthur')",
    )
    stufe: str | None = Field(
        default=None,
        max_length=100,
        description="Schulstufe filtern (z. B. 'Primarstufe', 'Sekundarstufe I')",
    )
    letzte_n_jahre: int = Field(
        default=5, ge=1, le=30, description="Anzahl der letzten Jahre (Standard: 5)"
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, strict=False)


class MittelschulenInput(BaseModel):
    """Input für Mittelschulstatistiken."""

    model_config = _STRICT

    mittelschultyp: str | None = Field(
        default=None,
        max_length=100,
        description="Schultyp filtern (z. B. 'Gymnasium', 'FMS', 'HMS')",
    )
    jahr: int | None = Field(default=None, description="Bestimmtes Jahr (leer = aktuellstes)")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, strict=False)
