"""Ashtakoota (Guna Milan) — 36-point North Indian matching."""
from __future__ import annotations

from ..core.chart import Chart
from ..core.reference import NAKSHATRAS, RASHI_LORDS, RASHIS, count_inclusive
from ..rules import v1 as R
from .common import band, envelope, nadi_exception, relation


def _vashya_group(chart: Chart) -> str:
    g = R.VASHYA_BY_RASHI[chart.moon.rashi]
    if isinstance(g, tuple):
        return g[0] if (chart.moon.longitude % 30.0) < 15.0 else g[1]
    return g


def _maitri_score(boy_lord: str, girl_lord: str) -> float:
    if boy_lord == girl_lord:
        return 5
    a, b = relation(boy_lord, girl_lord), relation(girl_lord, boy_lord)
    pair = sorted([a, b])
    table = {
        ("friend", "friend"): 5,
        ("friend", "neutral"): 4,
        ("neutral", "neutral"): 3,
        ("enemy", "friend"): 1,
        ("enemy", "neutral"): 0.5,
        ("enemy", "enemy"): 0,
    }
    return table[tuple(pair)]


def _tara_ok(from_nak: int, to_nak: int) -> tuple[bool, int]:
    c = count_inclusive(from_nak, to_nak, 27)
    t = ((c - 1) % 9) + 1
    return t not in R.TARA_BAD, t


def match(boy: Chart, girl: Chart) -> dict:
    bm, gm = boy.moon, girl.moon
    kootas = []

    # 1 Varna
    bv, gv = R.VARNA[bm.rashi], R.VARNA[gm.rashi]
    kootas.append({"name": "Varna", "score": 1 if bv >= gv else 0, "max": 1,
                   "boy": R.VARNA_NAMES[bv], "girl": R.VARNA_NAMES[gv]})

    # 2 Vashya
    bvs, gvs = _vashya_group(boy), _vashya_group(girl)
    vs = R.VASHYA_SCORE[R.VASHYA_ORDER.index(bvs)][R.VASHYA_ORDER.index(gvs)]
    kootas.append({"name": "Vashya", "score": vs, "max": 2,
                   "boy": R.VASHYA_NAMES[bvs], "girl": R.VASHYA_NAMES[gvs]})

    # 3 Tara (girl→boy and boy→girl)
    ok1, t1 = _tara_ok(gm.nakshatra, bm.nakshatra)
    ok2, t2 = _tara_ok(bm.nakshatra, gm.nakshatra)
    kootas.append({"name": "Tara", "score": 1.5 * ok1 + 1.5 * ok2, "max": 3,
                   "boy": f"Tara {t1} from girl", "girl": f"Tara {t2} from boy"})

    # 4 Yoni
    (ba, bg), (ga, gg) = R.YONI[bm.nakshatra], R.YONI[gm.nakshatra]
    ys = R.YONI_SCORE[R.YONI_ANIMALS.index(ba)][R.YONI_ANIMALS.index(ga)]
    kootas.append({"name": "Yoni", "score": ys, "max": 4, "boy": f"{ba} ({bg})", "girl": f"{ga} ({gg})"})

    # 5 Graha Maitri
    bl, gl = RASHI_LORDS[bm.rashi], RASHI_LORDS[gm.rashi]
    gms = _maitri_score(bl, gl)
    kootas.append({"name": "Graha Maitri", "score": gms, "max": 5, "boy": bl, "girl": gl})

    # 6 Gana
    bga, gga = R.GANA[bm.nakshatra], R.GANA[gm.nakshatra]
    gas = R.GANA_SCORE[(bga, gga)]
    kootas.append({"name": "Gana", "score": gas, "max": 6,
                   "boy": R.GANA_NAMES[bga], "girl": R.GANA_NAMES[gga]})

    # 7 Bhakoot
    c1 = count_inclusive(gm.rashi, bm.rashi, 12)
    c2 = count_inclusive(bm.rashi, gm.rashi, 12)
    bhakoot_bad = {c1, c2} in R.BHAKOOT_BAD_PAIRS
    kootas.append({"name": "Bhakoot", "score": 0 if bhakoot_bad else 7, "max": 7,
                   "boy": RASHIS[bm.rashi], "girl": RASHIS[gm.rashi], "note": f"{c1}/{c2} relationship"})

    # 8 Nadi
    bn, gn = R.NADI[bm.nakshatra], R.NADI[gm.nakshatra]
    nadi_bad = bn == gn
    kootas.append({"name": "Nadi", "score": 0 if nadi_bad else 8, "max": 8,
                   "boy": R.NADI_NAMES[bn], "girl": R.NADI_NAMES[gn]})

    # ------------------------------------------------------------- doshas
    doshas = []
    lords_friendly = bl == gl or (relation(bl, gl) == "friend" and relation(gl, bl) == "friend")

    if nadi_bad:
        reason = nadi_exception(bm, gm)
        doshas.append({"name": "Nadi", "status": "CANCELLED" if reason else "PRESENT", "reason": reason})
    else:
        doshas.append({"name": "Nadi", "status": "ABSENT", "reason": None})

    if bhakoot_bad:
        reason = "Rashi lords are the same or mutual friends" if lords_friendly else None
        doshas.append({"name": "Bhakoot", "status": "CANCELLED" if reason else "PRESENT", "reason": reason})
    else:
        doshas.append({"name": "Bhakoot", "status": "ABSENT", "reason": None})

    if gas == 0:
        reason = None
        if lords_friendly:
            reason = "Rashi lords are the same or mutual friends"
        elif not bhakoot_bad:
            reason = "Bhakoot is favourable"
        doshas.append({"name": "Gana", "status": "CANCELLED" if reason else "PRESENT", "reason": reason})
    else:
        doshas.append({"name": "Gana", "status": "ABSENT", "reason": None})

    raw_total = sum(k["score"] for k in kootas)
    # Doshas listed in ASHTAKOOTA_RESTORE_ON_CANCEL get their koota's full points back when cancelled
    restored = {"Nadi": 8, "Bhakoot": 7, "Gana": 6}
    for d in doshas:
        if d["status"] == "CANCELLED" and d["name"] in R.ASHTAKOOTA_RESTORE_ON_CANCEL:
            k = next(k for k in kootas if k["name"] == d["name"])
            k["rawScore"], k["score"] = k["score"], restored[d["name"]]
            k["note"] = (k.get("note") + "; " if k.get("note") else "") + "dosha cancelled — points restored"
    total = sum(k["score"] for k in kootas)
    # Informational: total if every cancelled dosha restored its points
    with_cancel = total + sum(restored[d["name"]] for d in doshas
                              if d["status"] == "CANCELLED" and d["name"] not in R.ASHTAKOOTA_RESTORE_ON_CANCEL)
    result, label = band(total, R.ASHTAKOOTA_BANDS)

    return envelope(
        "ASHTAKOOTA", result, label,
        score={"total": total, "max": 36, "rawTotal": raw_total, "totalWithCancellations": with_cancel},
        details={
            "kootas": kootas,
            "doshas": doshas,
            "boyNakshatra": NAKSHATRAS[bm.nakshatra],
            "girlNakshatra": NAKSHATRAS[gm.nakshatra],
        },
        warnings=[],
    )
