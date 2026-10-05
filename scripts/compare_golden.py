"""Compare the active ephemeris engine with the astrologer's printouts (tests/fixtures/private/golden_charts.json).

Usage:  python scripts/compare_golden.py
Prints, per chart, each planet/cusp: our degree, his degree, the difference in arc-seconds, and the
star/sub/sub-sub/sub-sub-sub lords on both sides (mismatches marked with *).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.ayanamsa import Ayanamsa  # noqa: E402
from app.core.chart import build_chart  # noqa: E402
from app.core.ephemeris import get_engine  # noqa: E402
from app.core.ephemeris.builtin import nutation  # noqa: E402
from app.core.reference import kp_lords  # noqa: E402
from app.core.timeutil import delta_t_seconds, parse_date, parse_time, to_utc  # noqa: E402

AB = {"Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me", "Jupiter": "Ju", "Venus": "Ve",
      "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke"}


def dms(x: float) -> str:
    total = round((x % 30) * 360000)  # hundredths of an arc-second, rounded once
    d, rem = divmod(total, 360000)
    m, cs = divmod(rem, 6000)
    return f"{d:02d}°{m:02d}'{cs / 100:05.2f}\""


def main() -> None:
    cases = json.loads((ROOT / "tests" / "fixtures" / "private" / "golden_charts.json").read_text(encoding="utf-8"))["charts"]
    eng = get_engine()
    print(f"engine: {eng.name}")
    for case in cases:
        t = to_utc(parse_date(case["dob"]), parse_time(case["tob"]), case.get("timezone", "Asia/Kolkata"),
                   case.get("utcOffset"))
        c = build_chart(t.jd_ut, case["lat"], case["lon"], Ayanamsa.KP)
        jd_tt = t.jd_ut + delta_t_seconds(t.jd_ut) / 86400
        print(f"\n=== {case['label']}")
        print(f"KP ayanamsa {c.ayanamsa_value:.6f}°   nutation Δψ {nutation(jd_tt)[0] * 3600:+.1f}\"")
        exp = case["expected"]
        pos = exp.get("positions", {})
        lords = exp.get("kp", {}).get("planetLords", {})
        print(f"{'':8} {'ours':>14} {'his':>14} {'diff(s)':>7}   ours lords     his lords")
        for name, (r, d, m, s) in pos.items():
            if name == "Lagna":
                continue
            theirs = r * 30 + d + m / 60 + s / 3600
            ours = c.planets[name].longitude
            diff = ((ours - theirs + 180) % 360 - 180) * 3600
            ol = " ".join(AB[x] for x in kp_lords(ours))
            hl = " ".join(lords.get(name, []))
            flag = " *" if hl and ol != hl else ""
            print(f"{name:8} {dms(ours):>14} {dms(theirs):>14} {diff:+7.1f}   {ol:14} {hl}{flag}")
        cusps = exp.get("kp", {}).get("cusps", [])
        clords = exp.get("kp", {}).get("cuspLords", [])
        for i, (r, d, m, s) in enumerate(cusps):
            theirs = r * 30 + d + m / 60 + s / 3600
            ours = c.cusps[i]
            diff = ((ours - theirs + 180) % 360 - 180) * 3600
            ol = " ".join(AB[x] for x in kp_lords(ours))
            hl = " ".join(clords[i]) if i < len(clords) else ""
            flag = " *" if hl and ol != hl else ""
            print(f"{'cusp ' + str(i + 1):8} {dms(ours):>14} {dms(theirs):>14} {diff:+7.1f}   {ol:14} {hl}{flag}")


if __name__ == "__main__":
    main()
