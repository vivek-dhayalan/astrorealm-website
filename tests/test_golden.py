"""Regression against astrologer-verified charts (tests/fixtures/golden_charts.json)
and, when pyswisseph is installed, a cross-check of the two ephemeris engines."""
import json
from pathlib import Path

import pytest

from app.core.ayanamsa import Ayanamsa
from app.core.chart import build_chart
from app.core.reference import NAKSHATRAS, RASHIS, sub_lord
from app.core.timeutil import parse_date, parse_time, to_utc

# Real people's verified birth data: kept out of the public repo (tests/fixtures/private/ is git-ignored)
_GOLDEN_FILE = Path(__file__).parent / "fixtures" / "private" / "golden_charts.json"
GOLDEN = json.loads(_GOLDEN_FILE.read_text(encoding="utf-8"))["charts"] if _GOLDEN_FILE.exists() else []


@pytest.mark.skipif(not GOLDEN, reason="Private verified charts not present")
@pytest.mark.parametrize("case", GOLDEN, ids=[c.get("label", str(i)) for i, c in enumerate(GOLDEN)])
def test_golden_chart(case):
    t = to_utc(parse_date(case["dob"]), parse_time(case["tob"]), case.get("timezone", "Asia/Kolkata"),
               case.get("utcOffset"))
    model = Ayanamsa(case.get("ayanamsa", "LAHIRI"))
    c = build_chart(t.jd_ut, case["lat"], case["lon"], model)
    exp = dict(case["expected"])
    positions = exp.pop("positions", {})
    tol = 3.0 if c.engine == "swisseph" else 10.0  # arcminutes
    for name, (ri, d, m, s) in positions.items():
        ours = c.ascendant if name == "Lagna" else c.planets[name].longitude
        theirs = ri * 30 + d + m / 60 + s / 3600
        diff = abs(((ours - theirs + 180) % 360) - 180) * 60
        assert diff <= tol, f"{name}: ours {ours:.4f} vs {theirs:.4f} ({diff:.1f}' > {tol}')"
    got = {
        "nakshatra": NAKSHATRAS[c.moon.nakshatra],
        "pada": c.moon.pada,
        "rashi": RASHIS[c.moon.rashi],
        "lagna": RASHIS[c.lagna_rashi],
    }
    retro = exp.pop("retrograde", None)
    if retro is not None:
        assert [k for k, v in c.planets.items() if v.retrograde and k not in ("Rahu", "Ketu")] == retro
    nav = exp.pop("navamsa", None)
    if nav:
        from app.core.reference import PADA_SPAN
        got_nav = {k: RASHIS[int((c.ascendant % 360) // PADA_SPAN) % 12] if k == "Lagna" else RASHIS[c.planets[k].navamsa]
                   for k in nav}
        assert got_nav == nav
    kp_exp = exp.pop("kp", None)
    if kp_exp:
        from app.matching import kp
        kc = build_chart(t.jd_ut, case["lat"], case["lon"], Ayanamsa.KP)
        for i, (ri, d, m, s) in enumerate(kp_exp.get("cusps", [])):
            theirs = ri * 30 + d + m / 60 + s / 3600
            diff = abs(((kc.cusps[i] - theirs + 180) % 360) - 180) * 3600
            assert diff <= 6, f"cusp {i + 1}: {diff:.0f}\" > 6\""
        ab = {"Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me", "Jupiter": "Ju", "Venus": "Ve",
              "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke"}
        from app.core.reference import kp_lords
        if "cuspLords" in kp_exp:
            assert [[ab[x] for x in kp_lords(c)] for c in kc.cusps] == kp_exp["cuspLords"]
        if "planetLords" in kp_exp:
            depth = 4 if kc.engine == "swisseph" else 2
            got_pl = {k: [ab[x] for x in kp_lords(kc.planets[k].longitude)][:depth] for k in kp_exp["planetLords"]}
            assert got_pl == {k: v[:depth] for k, v in kp_exp["planetLords"].items()}
        if "cuspSubLords" in kp_exp:
            assert [sub_lord(x) for x in kc.cusps] == kp_exp["cuspSubLords"]
        if "planetSignifications" in kp_exp:
            assert kp.planet_significations(kc) == kp_exp["planetSignifications"]
        a = kp.assess(kc)
        if "seventhSubLord" in kp_exp:
            assert a["subLord"] == kp_exp["seventhSubLord"]
        if "seventhSignifies" in kp_exp:
            assert a["signifies"] == kp_exp["seventhSignifies"]
    if "kp7thSubLord" in exp:
        got["kp7thSubLord"] = sub_lord(build_chart(t.jd_ut, case["lat"], case["lon"], Ayanamsa.KP).cusps[6])
    assert {k: got[k] for k in exp} == exp


SAMPLES = [  # (jd_ut, lat, lon)
    (2447931.1, 13.08, 80.27), (2448928.15, 9.92, 78.12), (2451545.0, 28.61, 77.21),
    (2440000.3, 19.07, 72.88), (2455000.7, 22.57, 88.36), (2460000.45, 51.5, -0.12),
]


@pytest.mark.parametrize("jd,lat,lon", SAMPLES)
def test_builtin_engine_agrees_with_swisseph(jd, lat, lon):
    pytest.importorskip("swisseph")
    from app.core.ephemeris import BuiltinEngine
    from app.core.ephemeris.swiss import SwissEngine

    b, s = BuiltinEngine(), SwissEngine()
    tol = {"Moon": 0.01, "Sun": 0.02, "Mercury": 0.05, "Venus": 0.05, "Mars": 0.05,
           "Jupiter": 0.2, "Saturn": 0.2, "Rahu": 0.01, "Ketu": 0.01}
    for model in Ayanamsa:
        assert b.ayanamsa(jd, model) == pytest.approx(s.ayanamsa(jd, model), abs=0.003)
        pb, ps = b.positions(jd, model), s.positions(jd, model)
        for k, t in tol.items():
            assert abs(((pb[k] - ps[k] + 180) % 360) - 180) < t, (model, k, pb[k], ps[k])
        hb, hs = b.houses(jd, lat, lon, model), s.houses(jd, lat, lon, model)
        for x, y in zip(hb.cusps, hs.cusps):
            assert abs(((x - y + 180) % 360) - 180) < 0.02
