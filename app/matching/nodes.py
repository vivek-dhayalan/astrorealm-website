"""Rahu / Ketu in the 7th, and Kala Sarpa — an advisory check, separate from Mangal dosha and never a veto."""
from __future__ import annotations

from ..core.chart import Chart
from ..core.reference import RASHIS, count_inclusive
from ..rules import v1 as R
from .common import envelope
from .dignity import seventh_lord, seventh_strong, seventh_weak, touches, venus_sound

NODES = ("Rahu", "Ketu")
_TEXT = {
    "MALEFIC_ON_NODE": "{planet} is with {node} or aspects it",
    "WEAK_7TH_LORD": "7th lord {lord} is weak (debilitated, or in the 6th, 8th or 12th)",
    "BENEFIC_ON_NODE": "{planet} is with {node} or aspects it",
    "STRONG_7TH_AND_VENUS": "7th lord {lord} and Venus are strong and unafflicted",
    "KALA_SARPA": "All planets lie on one side of the Rahu–Ketu axis (Kala Sarpa); many astrologers do not "
                  "treat this as a bar",
}


def _factor(code: str, effect: str, **params) -> dict:
    return {"code": code, "effect": effect, "params": params, "text": _TEXT[code].format(**params)}


def kala_sarpa(chart: Chart) -> bool:
    rahu = chart.planets["Rahu"].longitude
    arcs = [(chart.planets[p].longitude - rahu) % 360 for p in R.KALA_SARPA_PLANETS]
    return all(a < 180 for a in arcs) or all(a > 180 for a in arcs)


def assess(chart: Chart) -> dict:
    refs = {"lagna": chart.lagna_rashi, "moon": chart.moon.rashi}
    houses = {n: {k: count_inclusive(r, chart.planets[n].rashi, 12) for k, r in refs.items()} for n in NODES}
    in7 = [{"node": n, "ref": k} for n in NODES for k in refs if houses[n][k] == 7]
    notes = [_factor("KALA_SARPA", "NOTE")] if kala_sarpa(chart) else []
    base = {"houses": houses, "seventh": in7, "kalaSarpa": bool(notes),
            "rashi": {n: RASHIS[chart.planets[n].rashi] for n in NODES}}
    if not in7:
        return {**base, "status": "NONE", "factors": notes}

    main = max(in7, key=lambda e: R.NODE_7TH_WEIGHT[e["ref"]])
    node, sign = main["node"], chart.planets[main["node"]].rashi
    weight = R.NODE_7TH_WEIGHT[main["ref"]]
    factors = []
    for p in R.MALEFICS:
        if touches(chart, p, sign):
            weight += 1
            factors.append(_factor("MALEFIC_ON_NODE", "RAISES", planet=p, node=node))
            break
    if seventh_weak(chart):
        weight += 1
        factors.append(_factor("WEAK_7TH_LORD", "RAISES", lord=seventh_lord(chart)))
    for p in R.BENEFICS:
        if touches(chart, p, sign):
            weight -= 1
            factors.append(_factor("BENEFIC_ON_NODE", "LOWERS", planet=p, node=node))
            break
    if seventh_strong(chart) and venus_sound(chart):
        weight -= 1
        factors.append(_factor("STRONG_7TH_AND_VENUS", "LOWERS", lord=seventh_lord(chart)))
    status = "STRONG" if weight >= R.NODE_STRONG_AT else "MILD"  # reduced, never removed
    return {**base, "status": status, "factors": factors + notes}


_PAIR_LABEL = {
    "NO_DOSHA": "Neither has Rahu or Ketu in the 7th",
    "SHARED": "Both have Rahu or Ketu in the 7th — usually treated as balanced",
    "ONE_SIDED": "Only the {who} has Rahu or Ketu in the 7th",
}


def match(boy: Chart, girl: Chart) -> dict:
    b, g = assess(boy), assess(girl)
    active = lambda s: s["status"] != "NONE"  # noqa: E731
    who = None
    if active(b) and active(g):
        result = "SHARED"
    elif active(b) or active(g):
        result, who = "ONE_SIDED", ("boy" if active(b) else "girl")
    else:
        result = "NO_DOSHA"
    label = _PAIR_LABEL[result].format(who={"boy": "groom", "girl": "bride"}.get(who, ""))
    return envelope("RAHU_KETU", result, label, details={"who": who, "boy": b, "girl": g})
