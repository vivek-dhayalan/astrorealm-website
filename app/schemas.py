from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .core.ayanamsa import Ayanamsa
from .core.ephemeris.base import PositionMode
from .matching import Method


class Sex(str, Enum):
    M = "M"
    F = "F"


class PersonIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, max_length=80, description="Optional, display only — never used in calculations")
    sex: Sex
    dob: str = Field(..., description="Date of birth, YYYY-MM-DD", examples=["1991-09-23"])
    tob: str = Field(..., description="Time of birth: '19:45' (24h) or '07:45 PM' (12h)", examples=["06:30 AM"])
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)
    place: str | None = Field(None, description="Free-text place, e.g. 'Madurai, Tamil Nadu'")
    utcOffset: str | None = Field(
        None,
        description="Only used with lat/lon: overrides the time zone, e.g. '+05:30'. Ignored when 'place' is given.",
    )

    @field_validator("name", "place", "utcOffset", mode="before")
    @classmethod
    def _blank_is_none(cls, v):
        # Treat empty values and the Swagger placeholder "string" as not supplied
        if isinstance(v, str) and v.strip().lower() in ("", "string"):
            return None
        return v

    @model_validator(mode="after")
    def _location(self):
        has_coords = self.lat is not None or self.lon is not None
        if has_coords and (self.lat is None or self.lon is None):
            raise ValueError("Both lat and lon are required when using coordinates")
        if has_coords == bool(self.place):
            raise ValueError("Provide exactly one of lat/lon or place")
        return self


class Options(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI
    methods: list[Method] = Field(default_factory=lambda: list(Method))
    positions: PositionMode | None = Field(
        None, description="TRUE = true geometric planet positions (AstroWonder); APPARENT = as seen from Earth "
                          "(Swiss Ephemeris default). Defaults to the server setting (TRUE).")


class MatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    personA: PersonIn
    personB: PersonIn
    options: Options = Field(default_factory=Options)

    @model_validator(mode="after")
    def _sexes(self):
        if {self.personA.sex, self.personB.sex} != {Sex.M, Sex.F}:
            raise ValueError("Exactly one person must be 'M' and the other 'F'")
        return self


class ChartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    person: PersonIn
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI
    positions: PositionMode | None = Field(
        None, description="TRUE = true geometric planet positions (AstroWonder); APPARENT = as seen from Earth "
                          "(Swiss Ephemeris default). Defaults to the server setting (TRUE).")


class NamingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    person: PersonIn
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI
    names: list[Annotated[str, Field(max_length=60)]] = Field(
        default_factory=list, max_length=10,
        description="Candidate names to check (English spelling for the numbers). Not stored.")


class Language(str, Enum):
    en = "en"
    ta = "ta"
    te = "te"
    ml = "ml"
    kn = "kn"
    hi = "hi"


class ImagePart(str, Enum):
    RASI = "RASI"
    NAVAMSA = "NAVAMSA"
    KP_TABLES = "KP_TABLES"


class ChartImageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    person: PersonIn
    name: str | None = Field(None, max_length=80, deprecated=True,
                             description="Deprecated: use person.name. Kept for compatibility.")
    ayanamsa: Ayanamsa = Field(Ayanamsa.LAHIRI, description="For the Rasi/Navamsa charts; KP tables always use KP")
    lang: Language = Language.en
    include: list[ImagePart] = Field(default_factory=lambda: list(ImagePart))
    positions: PositionMode | None = Field(
        None, description="TRUE = true geometric planet positions (AstroWonder); APPARENT = as seen from Earth "
                          "(Swiss Ephemeris default). Defaults to the server setting (TRUE).")
