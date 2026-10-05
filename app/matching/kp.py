"""KP (Krishnamurti Paddhati) 7th-cusp sub-lord marriage promise."""
from __future__ import annotations

from ..core.ayanamsa import Ayanamsa
from ..core.chart import Chart, house_of
from ..core.ephemeris import get_engine
from ..core.reference import NAKSHATRA_LORDS, RASHI_LORDS, RASHIS, kp_lords, nakshatra_index, rashi_index, sub_lord
from ..rules import v1 as R
from .common import envelope

NODES = {"Rahu", "Ketu"}


def _owned(planet: str, cusps: list[float]) -> set[int]:
    return {i + 1 for i, c in enumerate(cusps) if RASHI_LORDS[rashi_index(c)] == planet}


def _planet_houses(chart: Chart, planet: str) -> tuple[set[int], set[int]]:
    """(occupied, owned) for a planet; nodes borrow ownership from their sign lord."""
    p = chart.planets[planet]
    occ = {p.house}
    if planet in NODES:
        disp = RASHI_LORDS[p.rashi]
        return occ | {chart.planets[disp].house}, _owned(disp, chart.cusps)
    return occ, _owned(planet, chart.cusps)


def significations_four_level(chart: Chart, planet: str) -> dict:
    """Classic 4-level union: star-lord's occupation/ownership + planet's own occupation/ownership."""
    p = chart.planets[planet]
    star_lord = NAKSHATRA_LORDS[p.nakshatra]
    sl_occ, sl_own = _planet_houses(chart, star_lord)
    occ, own = _planet_houses(chart, planet)
    levels = {
        "starLordOccupies": sorted(sl_occ),
        "occupies": sorted(occ),
        "starLordOwns": sorted(sl_own),
        "owns": sorted(own),
    }
    all_houses = set().union(sl_occ, occ, sl_own, own)
    return {"starLord": star_lord, "levels": levels, "houses": sorted(all_houses)}


def house_significators(chart: Chart) -> dict[int, list[str]]:
    """Significators per house, as the astrologer's software (AstroWonder) computes them:
    occupied house → planets in the star of each occupant (the occupant itself if none);
    empty house    → planets in the star of the cusp's sign lord (the lord itself if none)."""
    names = [p for p in chart.planets]
    star_of = {p: NAKSHATRA_LORDS[chart.planets[p].nakshatra] for p in names}

    def in_star_of(x: str) -> list[str]:
        return [p for p in names if star_of[p] == x]

    out: dict[int, list[str]] = {}
    for h in range(1, 13):
        occupants = [p for p in names if chart.planets[p].house == h]
        sources = occupants or [RASHI_LORDS[rashi_index(chart.cusps[h - 1])]]
        sig: list[str] = []
        for src in sources:
            for p in (in_star_of(src) or [src]):
                if p not in sig:
                    sig.append(p)
        out[h] = sig
    return out


def planet_significations(chart: Chart) -> dict[str, list[int]]:
    hs = house_significators(chart)
    return {p: sorted(h for h, ps in hs.items() if p in ps) for p in chart.planets}


def significations(chart: Chart, planet: str) -> dict:
    p = chart.planets[planet]
    star_lord = NAKSHATRA_LORDS[p.nakshatra]
    if R.KP_SIGNIFICATION_METHOD == "FOUR_LEVEL":
        return significations_four_level(chart, planet)
    return {"starLord": star_lord, "method": "HOUSE_SIGNIFICATORS",
            "houses": planet_significations(chart)[planet]}


def _promise(houses: set[int]) -> str:
    good = houses & R.KP_GOOD_HOUSES
    bad = houses & R.KP_BAD_HOUSES
    if not good:
        return "DENIED"
    if not bad:
        return "STRONG"
    if 7 not in houses:
        return "DENIED"
    if len(good) > len(bad):
        return "PROMISED"
    return "MIXED"


def _seventh_sub_lord_at(chart: Chart, minutes: float) -> str:
    eng = get_engine(chart.engine)
    hs = eng.houses(chart.jd_ut + minutes / 1440.0, chart.lat, chart.lon, Ayanamsa.KP)
    return sub_lord(hs.cusps[6])


def assess(chart: Chart) -> dict:
    if chart.ayanamsa != Ayanamsa.KP:
        raise ValueError("KP assessment needs a chart built with the KP ayanamsa")
    cusp7 = chart.cusps[6]
    sl = sub_lord(cusp7)
    sig = significations(chart, sl)
    promise = _promise(set(sig["houses"]))

    m = R.KP_SENSITIVITY_MINUTES
    before, after = _seventh_sub_lord_at(chart, -m), _seventh_sub_lord_at(chart, m)
    sensitive = before != sl or after != sl
    note = None
    if sensitive:
        changes = [f"{'-' if t < 0 else '+'}{m} min → {x}" for t, x in ((-m, before), (m, after)) if x != sl]
        note = "Sub-lord changes within ±%d min (%s)" % (m, ", ".join(changes))

    return {
        "cuspLongitude": round(cusp7, 4),
        "cuspRashi": RASHIS[rashi_index(cusp7)],
        "signLord": RASHI_LORDS[rashi_index(cusp7)],
        "starLord": NAKSHATRA_LORDS[nakshatra_index(cusp7)],
        "subLord": sl,
        "subSubLord": kp_lords(cusp7)[2],
        "subSubSubLord": kp_lords(cusp7)[3],
        "subLordStarLord": sig["starLord"],
        "significationMethod": sig.get("method", "FOUR_LEVEL"),
        **({"subLordSignificationLevels": sig["levels"]} if "levels" in sig else {}),
        "signifies": sig["houses"],
        "favourable": sorted(set(sig["houses"]) & R.KP_GOOD_HOUSES),
        "adverse": sorted(set(sig["houses"]) & R.KP_BAD_HOUSES),
        "promise": promise,
        "sensitive": sensitive,
        "sensitivity": note,
        "cusps": [
            {"house": i + 1, "longitude": round(c, 4), "rashi": RASHIS[rashi_index(c)],
             "signLord": RASHI_LORDS[rashi_index(c)], "starLord": NAKSHATRA_LORDS[nakshatra_index(c)],
             "subLord": sub_lord(c), "subSubLord": kp_lords(c)[2], "subSubSubLord": kp_lords(c)[3]}
            for i, c in enumerate(chart.cusps)
        ],
        "planetSignifications": planet_significations(chart),
    }


def match(boy: Chart, girl: Chart) -> dict:
    b, g = assess(boy), assess(girl)
    if b["sensitive"] or g["sensitive"]:
        result, label = "INCONCLUSIVE", "7th-cusp sub-lord is time-sensitive for at least one partner"
    else:
        denied = [x["promise"] == "DENIED" for x in (b, g)]
        if all(denied):
            result, label = "BOTH_DENIED", "Marriage not promised in either chart"
        elif any(denied):
            result, label = "ONE_DENIED", "Marriage not promised in one chart"
        else:
            result, label = "BOTH_PROMISED", "Marriage promised in both charts"
    return envelope(
        "KP_7TH_CUSP", result, label,
        details={"boy": b, "girl": g},
        warnings=["KP judges each person's marriage promise; it is not a compatibility score."],
    )


# re-exported for tests
__all__ = ["assess", "match", "significations", "house_of"]
