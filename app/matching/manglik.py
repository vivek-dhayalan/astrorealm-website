"""Mangal (Kuja / Chevvai) dosha — per person and per pair, in the South and North Indian traditions.

Each tradition is a rule set in app.rules.v1.MANGLIK_TRADITIONS. Results list the factors that
raised, lowered, reduced or cancelled the dosha, so the reasoning is visible rather than a bare verdict.
"""
from __future__ import annotations

from ..core.chart import Chart
from ..core.reference import RASHIS, count_inclusive
from ..rules import v1 as R
from .common import envelope
from .dignity import dignity, seventh_lord, seventh_strong, touches

TRADITIONS = ("SOUTH", "NORTH")
REF_NAMES = {"lagna": "Lagna", "moon": "Moon", "venus": "Venus"}

_TEXT = {
    "OWN_OR_EXALTED": "Mars in its own or exaltation sign ({sign})",
    "JUPITER_ASPECT": "Jupiter is with Mars or aspects it",
    "WITH_JUPITER": "Jupiter is with Mars",
    "HOUSE_SIGN_EXCEPTION": "Mars in house {house} from {ref} in {sign} is a listed exception",
    "WITH_MOON": "Moon is with Mars",
    "STRONG_7TH_LORD": "Strong 7th house (7th lord {lord} well placed or Jupiter on the 7th)",
    "MOVABLE_SIGN": "Mars in a movable sign ({sign})",
    "FRIENDLY_SIGN": "Mars in a friendly sign ({sign})",
    "DEBILITATED": "Mars debilitated ({sign})",
    "ENEMY_SIGN": "Mars in an enemy sign ({sign})",
    "SATURN_ON_MARS": "Saturn is with Mars or aspects it",
    "ALL_THREE": "Present from Lagna, Moon and Venus",
    "PARTIAL": "Present only from {refs}, not from Lagna (partial)",
}


def _factor(code: str, effect: str, **params) -> dict:
    return {"code": code, "effect": effect, "params": params, "text": _TEXT[code].format(**params)}


def _refs(chart: Chart) -> dict[str, int]:
    return {"lagna": chart.lagna_rashi, "moon": chart.moon.rashi, "venus": chart.planets["Venus"].rashi}


def assess(chart: Chart, tradition: str = "SOUTH") -> dict:
    rules = R.MANGLIK_TRADITIONS[tradition]
    mars = chart.planets["Mars"]
    sign = RASHIS[mars.rashi]
    refs = _refs(chart)
    houses = {k: count_inclusive(refs[k], mars.rashi, 12) for k in rules["refs"]}
    present = [k for k, h in houses.items() if h in R.MANGLIK_HOUSES]
    base = {"tradition": tradition, "mars": {"rashi": sign, "dignity": dignity("Mars", mars.rashi)},
            "houses": houses, "presentFrom": present}
    if not present:
        return {**base, "status": "NONE", "grade": None, "factors": []}

    factors: list[dict] = []
    if "lagna" in present:
        weight = R.MANGLIK_HOUSE_WEIGHT[houses["lagna"]]
        if len(present) == 3:
            weight += 1
            factors.append(_factor("ALL_THREE", "RAISES"))
    else:
        weight = 1  # only from Moon / Venus: partial
        factors.append(_factor("PARTIAL", "LOWERS", refs=" / ".join(REF_NAMES[k] for k in present)))
    dig = base["mars"]["dignity"]
    if dig == "FRIEND":
        weight -= 1
        factors.append(_factor("FRIENDLY_SIGN", "LOWERS", sign=sign))
    elif dig == "DEBILITATED":
        weight += 1
        factors.append(_factor("DEBILITATED", "RAISES", sign=sign))
    elif dig == "ENEMY":
        weight += 1
        factors.append(_factor("ENEMY_SIGN", "RAISES", sign=sign))
    if touches(chart, "Saturn", mars.rashi):
        weight += 1
        factors.append(_factor("SATURN_ON_MARS", "RAISES"))
    if "lagna" not in present:
        weight = min(weight, 1)
    grade = "STRONG" if weight >= R.MANGLIK_STRONG_AT else "MILD"

    cancels: list[dict] = []
    if "OWN_OR_EXALTED" in rules["cancel"] and mars.rashi in R.MARS_OWN_OR_EXALTED:
        cancels.append(_factor("OWN_OR_EXALTED", "CANCELS", sign=sign))
    if "WITH_JUPITER" in rules["cancel"] and chart.planets["Jupiter"].rashi == mars.rashi:
        cancels.append(_factor("WITH_JUPITER", "CANCELS"))
    if "JUPITER_ASPECT" in rules["cancel"] and touches(chart, "Jupiter", mars.rashi):
        cancels.append(_factor("JUPITER_ASPECT", "CANCELS"))
    if "HOUSE_SIGN_EXCEPTION" in rules["cancel"]:
        for k in present:
            if mars.rashi in R.MANGLIK_HOUSE_SIGN_EXCEPTIONS.get(houses[k], set()):
                cancels.append(_factor("HOUSE_SIGN_EXCEPTION", "CANCELS", house=houses[k], ref=REF_NAMES[k],
                                       sign=sign))
    if "WITH_MOON" in rules["cancel"] and chart.moon.rashi == mars.rashi:
        cancels.append(_factor("WITH_MOON", "CANCELS"))

    reduces: list[dict] = []
    if "STRONG_7TH_LORD" in rules["reduce"] and seventh_strong(chart):
        reduces.append(_factor("STRONG_7TH_LORD", "REDUCES", lord=seventh_lord(chart)))
    if "MOVABLE_SIGN" in rules["reduce"] and mars.rashi in R.MOVABLE_SIGNS:
        reduces.append(_factor("MOVABLE_SIGN", "REDUCES", sign=sign))

    if cancels:
        status = "CANCELLED"
    elif reduces:
        status = "MILD"  # reduced, never removed
    else:
        status = grade
    return {**base, "status": status, "grade": grade, "factors": factors + reduces + cancels}


_PAIR_LABEL = {
    "NO_DOSHA": "Neither partner has it",
    "CANCELLED": "Present but cancelled",
    "MUTUAL": "Both have it to a similar degree — treated as balanced",
    "PARTLY_BALANCED": "Both have it, one more strongly — partly balanced",
    "ONE_SIDED": "Only the {who} has it",
}


def pair(b: dict, g: dict) -> dict:
    active = lambda s: s["status"] in ("MILD", "STRONG")  # noqa: E731
    who = None
    if active(b) and active(g):
        result = "MUTUAL" if b["status"] == g["status"] else "PARTLY_BALANCED"
    elif active(b) or active(g):
        result, who = "ONE_SIDED", ("boy" if active(b) else "girl")
    elif b["status"] == "CANCELLED" or g["status"] == "CANCELLED":
        result = "CANCELLED"
    else:
        result = "NO_DOSHA"
    label = _PAIR_LABEL[result].format(who={"boy": "groom", "girl": "bride"}.get(who, ""))
    return {"result": result, "label": label, "who": who, "boy": b, "girl": g}


def match(boy: Chart, girl: Chart) -> dict:
    views = {t.lower(): pair(assess(boy, t), assess(girl, t)) for t in TRADITIONS}
    warnings = []
    for who, ch in (("boy", boy), ("girl", girl)):
        if any("Lagna" in w for w in ch.warnings):
            warnings.append(f"{who}: Lagna near sign boundary; Mangal dosha from Lagna is time-sensitive.")
    south = views["south"]
    return envelope("MANGLIK", south["result"], f"South Indian: {south['label']}", details=views,
                    warnings=warnings)
