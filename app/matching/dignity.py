"""Sign dignity and whole-sign aspects, shared by the dosha checks."""
from __future__ import annotations

from ..core.chart import Chart
from ..core.reference import RASHI_LORDS, count_inclusive
from ..rules import v1 as R
from .common import relation


def dignity(planet: str, rashi: int) -> str:
    """OWN | EXALTED | DEBILITATED | FRIEND | NEUTRAL | ENEMY for a planet in a sign."""
    if RASHI_LORDS[rashi] == planet:
        return "OWN"
    ex = R.EXALTATION.get(planet)
    if ex is not None and rashi == ex:
        return "EXALTED"
    if ex is not None and rashi == (ex + 6) % 12:
        return "DEBILITATED"
    rel = relation(planet, RASHI_LORDS[rashi])
    return {"friend": "FRIEND", "enemy": "ENEMY"}.get(rel, "NEUTRAL")


def aspects(chart: Chart, planet: str, rashi: int) -> bool:
    """Does the planet aspect this sign (whole-sign graha drishti)? Being in the sign is not an aspect."""
    n = count_inclusive(chart.planets[planet].rashi, rashi, 12)
    return n == 7 or n in R.SPECIAL_ASPECTS.get(planet, set())


def touches(chart: Chart, planet: str, rashi: int) -> bool:
    """In the sign or aspecting it."""
    return chart.planets[planet].rashi == rashi or aspects(chart, planet, rashi)


def house_sign(chart: Chart, house: int) -> int:
    """Sign of a whole-sign house counted from the Lagna."""
    return (chart.lagna_rashi + house - 1) % 12


def seventh_lord(chart: Chart) -> str:
    return RASHI_LORDS[house_sign(chart, 7)]


def seventh_strong(chart: Chart) -> bool:
    """7th lord in its own or exaltation sign, or Jupiter in or aspecting the 7th."""
    lord = seventh_lord(chart)
    return (dignity(lord, chart.planets[lord].rashi) in ("OWN", "EXALTED")
            or touches(chart, "Jupiter", house_sign(chart, 7)))


def seventh_weak(chart: Chart) -> bool:
    """7th lord debilitated, or in the 6th, 8th or 12th from the Lagna."""
    lord = seventh_lord(chart)
    p = chart.planets[lord]
    return (dignity(lord, p.rashi) == "DEBILITATED"
            or count_inclusive(chart.lagna_rashi, p.rashi, 12) in (6, 8, 12))


def venus_sound(chart: Chart) -> bool:
    """Venus not debilitated and not sharing a sign with Mars, Saturn, Rahu or Ketu."""
    v = chart.planets["Venus"]
    return (dignity("Venus", v.rashi) != "DEBILITATED"
            and all(chart.planets[p].rashi != v.rashi for p in ("Mars", "Saturn", "Rahu", "Ketu")))
