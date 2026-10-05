"""Swiss Ephemeris engine (pyswisseph). Uses the built-in Moshier ephemeris unless
SE_EPHE_PATH points at Swiss .se1 files, which are used automatically."""
from __future__ import annotations

import os
import threading

import swisseph as swe  # type: ignore

from ..ayanamsa import Ayanamsa
from ..reference import norm360
from .base import DEFAULT_POSITION_MODE, EphemerisEngine, HouseResult, PositionMode

_LOCK = threading.Lock()  # swisseph keeps global sidereal-mode state
_SID = {Ayanamsa.LAHIRI: swe.SIDM_LAHIRI, Ayanamsa.KP: swe.SIDM_KRISHNAMURTI}
_BODIES = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE,
}

_path = os.environ.get("SE_EPHE_PATH")
_FLAGS = swe.FLG_SWIEPH if _path else swe.FLG_MOSEPH
if _path:
    swe.set_ephe_path(_path)


class SwissEngine(EphemerisEngine):
    name = "swisseph"

    def ayanamsa(self, jd_ut: float, model: Ayanamsa) -> float:
        with _LOCK:
            swe.set_sid_mode(_SID[model], 0, 0)
            return swe.get_ayanamsa_ut(jd_ut)

    def positions(self, jd_ut: float, model: Ayanamsa,
                  mode: PositionMode = DEFAULT_POSITION_MODE) -> dict[str, float]:
        flags = _FLAGS | swe.FLG_SIDEREAL | (swe.FLG_TRUEPOS if mode == PositionMode.TRUE else 0)
        out: dict[str, float] = {}
        with _LOCK:
            swe.set_sid_mode(_SID[model], 0, 0)
            for name, body in _BODIES.items():
                res = swe.calc_ut(jd_ut, body, flags)
                xx = res[0] if isinstance(res[0], (list, tuple)) else res
                out[name] = norm360(xx[0])
        out["Ketu"] = norm360(out["Rahu"] + 180)
        return out

    def houses(self, jd_ut: float, lat: float, lon: float, model: Ayanamsa) -> HouseResult:
        with _LOCK:
            swe.set_sid_mode(_SID[model], 0, 0)
            cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, b"P", swe.FLG_SIDEREAL)
        cusps = list(cusps)
        if len(cusps) == 13:  # very old pyswisseph returned a dummy cusps[0]
            cusps = cusps[1:]
        return HouseResult(ascendant=norm360(ascmc[0]), mc=norm360(ascmc[1]), cusps=[norm360(c) for c in cusps])
