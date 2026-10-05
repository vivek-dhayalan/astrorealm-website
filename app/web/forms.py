"""Parse and validate the website's HTML forms (urlencoded bodies, no extra dependencies)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from urllib.parse import parse_qs

from ..core.ayanamsa import Ayanamsa
from ..schemas import PersonIn, Sex
from .sanitize import clean_html
from .strings import LANGS

MAX_BODY = 64 * 1024
CHART_PARTS = ("RASI", "NAVAMSA", "KP_TABLES")
DEFAULT_PARTS = ("RASI", "NAVAMSA")


def parse_body(body: bytes) -> dict[str, list[str]]:
    if len(body) > MAX_BODY:
        raise ValueError("Form is too large.")
    return parse_qs(body.decode("utf-8", errors="replace"), keep_blank_values=True, max_num_fields=200)


def _one(f: dict, key: str, max_len: int = 200) -> str:
    v = (f.get(key) or [""])[0]
    return v.strip()[:max_len]


def _int(f: dict, key: str, lo: int = 0, hi: int = 20) -> int | None:
    v = _one(f, key, 3)
    if not v:
        return None
    try:
        return max(lo, min(hi, int(v)))
    except ValueError:
        return None


def _float(f: dict, key: str) -> float | None:
    v = _one(f, key, 32)
    try:
        return float(v) if v else None
    except ValueError:
        return None


_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")


@dataclass
class BirthInput:
    name: str = ""
    sex: str = ""
    dob: str = ""
    tob: str = ""
    place: str = ""
    lat: float | None = None
    lon: float | None = None

    def validate(self, prefix: str, errors: dict[str, str], require_name: bool = True) -> None:
        if require_name and not self.name:
            errors[prefix + "name"] = "Please enter the name."
        if self.sex not in ("M", "F"):
            errors[prefix + "sex"] = "Please choose male or female."
        if not _DATE.match(self.dob):
            errors[prefix + "dob"] = "Please enter the date of birth."
        else:
            try:
                d = date.fromisoformat(self.dob)
                if not (1800 <= d.year <= 2100):
                    errors[prefix + "dob"] = "Date must be between 1800 and 2100."
            except ValueError:
                errors[prefix + "dob"] = "That date doesn't exist."
        if not _TIME.match(self.tob):
            errors[prefix + "tob"] = "Please enter the time of birth."
        has_coords = self.lat is not None and self.lon is not None
        if has_coords and not (-90 <= self.lat <= 90 and -180 <= self.lon <= 180):
            errors[prefix + "place"] = "The map location is out of range."
        if not has_coords and not self.place:
            errors[prefix + "place"] = "Please choose the place of birth."

    def to_person(self) -> PersonIn:
        if self.lat is not None and self.lon is not None:
            return PersonIn(name=self.name or None, sex=Sex(self.sex), dob=self.dob, tob=self.tob,
                            lat=self.lat, lon=self.lon)
        return PersonIn(name=self.name or None, sex=Sex(self.sex), dob=self.dob, tob=self.tob, place=self.place)


def _birth(f: dict, prefix: str = "", sex: str | None = None) -> BirthInput:
    return BirthInput(
        name=_one(f, prefix + "name", 80),
        sex=sex or _one(f, prefix + "sex", 1),
        dob=_one(f, prefix + "dob", 10),
        tob=_one(f, prefix + "tob", 8),
        place=_one(f, prefix + "place", 120),
        lat=_float(f, prefix + "lat"),
        lon=_float(f, prefix + "lon"),
    )


def _lang(f: dict) -> str:
    v = _one(f, "lang", 2)
    return v if v in LANGS else "en"


def _ayanamsa(f: dict) -> Ayanamsa:
    v = _one(f, "ayanamsa", 10).upper()
    return Ayanamsa(v) if v in Ayanamsa.__members__ else Ayanamsa.LAHIRI


@dataclass
class HoroscopeForm:
    birth: BirthInput = field(default_factory=BirthInput)
    lang: str = "en"
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI
    parts: tuple[str, ...] = DEFAULT_PARTS
    gothram: str = ""
    mathulam: str = ""
    father: str = ""
    mother: str = ""
    brothers: int | None = None
    brothers_married: int | None = None
    sisters: int | None = None
    sisters_married: int | None = None
    complexion: str = ""
    degree: str = ""
    branch: str = ""
    occupation: str = ""
    description: str = ""
    errors: dict[str, str] = field(default_factory=dict)

    @classmethod
    def parse(cls, f: dict) -> "HoroscopeForm":
        parts = tuple(p for p in CHART_PARTS if p in (f.get("parts") or []))
        frm = cls(
            birth=_birth(f),
            lang=_lang(f),
            ayanamsa=_ayanamsa(f),
            parts=parts,
            gothram=_one(f, "gothram", 40),
            mathulam=_one(f, "mathulam", 40),
            father=_one(f, "father", 10) if _one(f, "father", 10) in ("living", "deceased") else "",
            mother=_one(f, "mother", 10) if _one(f, "mother", 10) in ("living", "deceased") else "",
            brothers=_int(f, "brothers"),
            brothers_married=_int(f, "brothers_married"),
            sisters=_int(f, "sisters"),
            sisters_married=_int(f, "sisters_married"),
            complexion=_one(f, "complexion", 40),
            degree=_one(f, "degree", 80),
            branch=_one(f, "branch", 80),
            occupation=_one(f, "occupation", 120),
            description=clean_html((f.get("description") or [""])[0]),
        )
        frm.birth.validate("", frm.errors)
        if not frm.parts:
            frm.errors["parts"] = "Choose at least one chart."
        for k in ("brothers", "sisters"):
            n, m = getattr(frm, k), getattr(frm, k + "_married")
            if m is not None and (n is None or m > n):
                frm.errors[k] = "Married count can't be more than the total."
        return frm


@dataclass
class MatchForm:
    bride: BirthInput = field(default_factory=lambda: BirthInput(sex="F"))
    groom: BirthInput = field(default_factory=lambda: BirthInput(sex="M"))
    lang: str = "en"
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI
    errors: dict[str, str] = field(default_factory=dict)

    @classmethod
    def parse(cls, f: dict) -> "MatchForm":
        frm = cls(bride=_birth(f, "b_", "F"), groom=_birth(f, "g_", "M"), lang=_lang(f), ayanamsa=_ayanamsa(f))
        frm.bride.validate("b_", frm.errors)
        frm.groom.validate("g_", frm.errors)
        return frm
