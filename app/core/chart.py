"""Builds a sidereal birth chart from resolved time and place."""
from __future__ import annotations

from dataclasses import dataclass, field

from .ayanamsa import Ayanamsa
from .ephemeris import EphemerisEngine, get_engine
from .ephemeris.base import DEFAULT_POSITION_MODE, PositionMode
from .reference import (
    NAKSHATRA_LORDS, NAKSHATRA_SPAN, NAKSHATRAS, PADA_SPAN, RASHI_ENGLISH, RASHI_LORDS, RASHI_SPAN, RASHIS,
    distance_to_boundary, kp_lords, nakshatra_index, norm360, pada, rashi_index, sub_lord,
)

MOON_BOUNDARY_WARN_DEG = 0.25   # ≈ 30 min of birth time
LAGNA_BOUNDARY_WARN_DEG = 1.0   # ≈ 4 min of birth time


@dataclass
class PlanetPos:
    name: str
    longitude: float
    rashi: int
    nakshatra: int
    pada: int
    sub_lord: str
    house: int | None = None  # Placidus house (1..12)
    retrograde: bool = False

    @property
    def kp(self) -> list[str]:
        """[star, sub, sub-sub, sub-sub-sub] lords."""
        return kp_lords(self.longitude, 4)

    @property
    def navamsa(self) -> int:
        """D9 sign index (continuous count from Mesha; equivalent to the movable/fixed/dual rule)."""
        return int(norm360(self.longitude) // PADA_SPAN) % 12

    def to_dict(self) -> dict:
        return {
            "longitude": round(self.longitude, 4),
            "rashi": RASHIS[self.rashi],
            "nakshatra": NAKSHATRAS[self.nakshatra],
            "pada": self.pada,
            "signLord": RASHI_LORDS[self.rashi],
            "starLord": NAKSHATRA_LORDS[self.nakshatra],
            "subLord": self.sub_lord,
            "subSubLord": self.kp[2],
            "subSubSubLord": self.kp[3],
            "house": self.house,
            "retrograde": self.retrograde,
            "navamsa": RASHIS[self.navamsa],
        }


@dataclass
class Chart:
    ayanamsa: Ayanamsa
    ayanamsa_value: float
    engine: str
    jd_ut: float
    lat: float
    lon: float
    planets: dict[str, PlanetPos]
    ascendant: float
    cusps: list[float]
    warnings: list[str] = field(default_factory=list)
    position_mode: PositionMode = DEFAULT_POSITION_MODE
    position_sensitive: list[dict] = field(default_factory=list)

    @property
    def moon(self) -> PlanetPos:
        return self.planets["Moon"]

    @property
    def lagna_rashi(self) -> int:
        return rashi_index(self.ascendant)

    def to_dict(self) -> dict:
        m = self.moon
        return {
            "nakshatra": NAKSHATRAS[m.nakshatra],
            "nakshatraLord": NAKSHATRA_LORDS[m.nakshatra],
            "pada": m.pada,
            "rashi": RASHIS[m.rashi],
            "rashiEnglish": RASHI_ENGLISH[m.rashi],
            "rashiLord": RASHI_LORDS[m.rashi],
            "moonLongitude": round(m.longitude, 4),
            "lagna": RASHIS[self.lagna_rashi],
            "lagnaNavamsa": RASHIS[int(norm360(self.ascendant) // PADA_SPAN) % 12],
            "lagnaLongitude": round(self.ascendant, 4),
            "ayanamsa": self.ayanamsa.value,
            "ayanamsaValue": round(self.ayanamsa_value, 6),
            "engine": self.engine,
            "positions": self.position_mode.value,
            "positionSensitive": list(self.position_sensitive),
            "planets": {k: v.to_dict() for k, v in self.planets.items()},
            "warnings": list(self.warnings),
        }


def house_of(lon: float, cusps: list[float]) -> int:
    lon = norm360(lon)
    for i in range(12):
        start, end = cusps[i], cusps[(i + 1) % 12]
        span = (end - start) % 360
        if (lon - start) % 360 < span:
            return i + 1
    return 12


LEVELS = ["star", "sub", "subSub", "subSubSub"]


def build_chart(jd_ut: float, lat: float, lon: float, model: Ayanamsa = Ayanamsa.LAHIRI,
                engine: EphemerisEngine | None = None, positions: PositionMode | None = None) -> Chart:
    eng = engine or get_engine()
    mode = positions or DEFAULT_POSITION_MODE
    pos = eng.positions(jd_ut, model, mode)
    before, after = eng.positions(jd_ut - 0.25, model, mode), eng.positions(jd_ut + 0.25, model, mode)
    hs = eng.houses(jd_ut, lat, lon, model)
    planets = {
        name: PlanetPos(name, lng, rashi_index(lng), nakshatra_index(lng), pada(lng), sub_lord(lng),
                        house_of(lng, hs.cusps),
                        retrograde=((after[name] - before[name] + 180) % 360 - 180) < 0)
        for name, lng in pos.items()
    }
    warnings: list[str] = []
    moon = pos["Moon"]
    d_nak = distance_to_boundary(moon, NAKSHATRA_SPAN)
    if d_nak < MOON_BOUNDARY_WARN_DEG:
        kind = "rashi and nakshatra" if distance_to_boundary(moon, RASHI_SPAN) < MOON_BOUNDARY_WARN_DEG else "nakshatra"
        warnings.append(
            f"Moon is {d_nak * 60:.1f}' from a {kind} boundary; a birth-time error of ~{d_nak / 0.55 * 60:.0f} min would change it."
        )
    elif distance_to_boundary(moon, PADA_SPAN) < MOON_BOUNDARY_WARN_DEG / 2:
        warnings.append("Moon is close to a pada boundary; pada may change with a small birth-time error.")
    if distance_to_boundary(hs.ascendant, RASHI_SPAN) < LAGNA_BOUNDARY_WARN_DEG:
        warnings.append("Lagna is within 1° of a sign boundary; Mangal dosha from Lagna is time-sensitive.")

    # Would the other position convention (true vs apparent) change any KP lord?
    other = PositionMode.APPARENT if mode == PositionMode.TRUE else PositionMode.TRUE
    alt = eng.positions(jd_ut, model, other)
    sensitive: list[dict] = []
    for name, lng in pos.items():
        a, b = kp_lords(lng), kp_lords(alt[name])
        for lvl, (x, y) in enumerate(zip(a, b)):
            if x != y:
                sensitive.append({"planet": name, "level": LEVELS[lvl], mode.value.lower(): x, other.value.lower(): y})
                break
    if sensitive:
        warnings.append(
            "With " + other.value + " positions these lords would differ: "
            + "; ".join(f"{d['planet']} {d['level']} {d[mode.value.lower()]}→{d[other.value.lower()]}" for d in sensitive)
        )
    return Chart(
        ayanamsa=model,
        ayanamsa_value=eng.ayanamsa(jd_ut, model),
        engine=eng.name,
        jd_ut=jd_ut,
        lat=lat,
        lon=lon,
        planets=planets,
        ascendant=hs.ascendant,
        cusps=hs.cusps,
        warnings=warnings,
        position_mode=mode,
        position_sensitive=sensitive,
    )
