"""Mangal (Kuja) dosha — per person and pair compatibility."""
from __future__ import annotations

from ..core.chart import Chart
from ..core.reference import RASHIS, count_inclusive
from ..rules import v1 as R
from .common import envelope


def assess(chart: Chart) -> dict:
    mars = chart.planets["Mars"]
    refs = {
        "fromLagna": chart.lagna_rashi,
        "fromMoon": chart.moon.rashi,
        "fromVenus": chart.planets["Venus"].rashi,
    }
    houses = {k: count_inclusive(v, mars.rashi, 12) for k, v in refs.items()}
    afflicted = {k: h for k, h in houses.items() if h in R.MANGLIK_HOUSES}

    if not afflicted:
        return {"status": "NONE", "marsRashi": RASHIS[mars.rashi], "marsHouse": houses,
                "afflictedFrom": [], "cancellations": []}

    level = "HIGH" if "fromLagna" in afflicted else "LOW"
    cancellations: list[str] = []
    if mars.rashi in R.MARS_OWN_OR_EXALTED:
        cancellations.append(f"Mars in own/exalted sign ({RASHIS[mars.rashi]})")
    for ref, h in afflicted.items():
        if mars.rashi in R.MANGLIK_HOUSE_SIGN_EXCEPTIONS.get(h, set()):
            cancellations.append(f"Mars in house {h} {ref} in {RASHIS[mars.rashi]}")
    for p in R.MANGLIK_CANCEL_CONJUNCT:
        if chart.planets[p].rashi == mars.rashi:
            cancellations.append(f"Mars conjunct {p}")

    status = "CANCELLED" if cancellations else level
    return {"status": status, "doshaLevel": level, "marsRashi": RASHIS[mars.rashi], "marsHouse": houses,
            "afflictedFrom": sorted(afflicted), "cancellations": cancellations}


def match(boy: Chart, girl: Chart) -> dict:
    b, g = assess(boy), assess(girl)
    active = lambda s: s["status"] in ("LOW", "HIGH")  # noqa: E731
    if active(b) and active(g):
        result, label = "MUTUAL", "Both Manglik — dosha neutralised"
    elif active(b) or active(g):
        result, label = "MISMATCH", "Only one partner has an uncancelled Mangal dosha"
    elif b["status"] == "CANCELLED" or g["status"] == "CANCELLED":
        result, label = "CANCELLED", "Dosha present but cancelled"
    else:
        result, label = "NO_DOSHA", "Neither partner has Mangal dosha"
    warnings = []
    for who, ch in (("boy", boy), ("girl", girl)):
        if any("Lagna" in w for w in ch.warnings):
            warnings.append(f"{who}: Lagna near sign boundary; Mangal dosha from Lagna is time-sensitive.")
    return envelope("MANGLIK", result, label, details={"boy": b, "girl": g}, warnings=warnings)
