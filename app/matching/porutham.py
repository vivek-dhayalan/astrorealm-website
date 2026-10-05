"""Porutham — South Indian matching (12 checks; counts from girl to boy)."""
from __future__ import annotations

from ..core.chart import Chart
from ..core.reference import NAKSHATRAS, RASHI_LORDS, RASHIS, count_inclusive
from ..rules import v1 as R
from .common import envelope, nadi_exception, relation

MATCH, PARTIAL, NO_MATCH = "MATCH", "PARTIAL", "NO_MATCH"


def _item(name: str, status: str, reason: str, critical: bool = False) -> dict:
    return {"name": name, "status": status, "critical": critical, "reason": reason}


def match(boy: Chart, girl: Chart) -> dict:
    b, g = boy.moon, girl.moon
    star_count = count_inclusive(g.nakshatra, b.nakshatra, 27)
    rasi_count = count_inclusive(g.rashi, b.rashi, 12)
    items = []

    # 1 Dina
    if star_count in R.DINA_MATCH_COUNTS:
        st = MATCH
    elif star_count in R.DINA_PARTIAL_COUNTS:
        st = PARTIAL
    else:
        st = NO_MATCH
    items.append(_item("Dina", st, f"Boy's star is {star_count} from girl's"))

    # 2 Gana
    bg, gg = R.GANA[b.nakshatra], R.GANA[g.nakshatra]
    if bg == gg or (bg == "D" and gg == "M"):
        st = MATCH
    elif bg == "M" and gg == "D":
        st = PARTIAL
    else:
        st = NO_MATCH
    items.append(_item("Gana", st, f"Boy {R.GANA_NAMES[bg]}, girl {R.GANA_NAMES[gg]}"))

    # 3 Mahendra
    st = MATCH if star_count in R.MAHENDRA_COUNTS else NO_MATCH
    items.append(_item("Mahendra", st, f"Boy's star is {star_count} from girl's"))

    # 4 Stree Deergha
    if star_count >= R.STREE_DEERGHA_MATCH_MIN:
        st = MATCH
    elif star_count >= R.STREE_DEERGHA_PARTIAL_MIN:
        st = PARTIAL
    else:
        st = NO_MATCH
    items.append(_item("Stree Deergha", st, f"Boy's star is {star_count} from girl's"))

    # 5 Yoni
    (ba, _), (ga, _) = R.YONI[b.nakshatra], R.YONI[g.nakshatra]
    ys = R.YONI_SCORE[R.YONI_ANIMALS.index(ba)][R.YONI_ANIMALS.index(ga)]
    st = MATCH if ys >= 3 else PARTIAL if ys >= 1 else NO_MATCH
    items.append(_item("Yoni", st, f"Boy {ba}, girl {ga}" + (" (enemy yonis)" if ys == 0 else "")))

    # 6 Rasi
    if rasi_count == 1 and b.nakshatra == g.nakshatra:
        st = PARTIAL
    elif rasi_count in R.RASI_MATCH_COUNTS:
        st = MATCH
    elif rasi_count in R.RASI_PARTIAL_COUNTS:
        st = PARTIAL
    else:
        st = NO_MATCH
    items.append(_item("Rasi", st, f"Boy's rasi ({RASHIS[b.rashi]}) is {rasi_count} from girl's ({RASHIS[g.rashi]})"))

    # 7 Rasyadhipathi
    bl, gl = RASHI_LORDS[b.rashi], RASHI_LORDS[g.rashi]
    rels = {relation(bl, gl), relation(gl, bl)}
    if bl == gl or rels == {"friend"}:
        st = MATCH
    elif "enemy" in rels:
        st = NO_MATCH
    else:
        st = PARTIAL
    items.append(_item("Rasyadhipathi", st, f"Lords {bl} (boy) and {gl} (girl)"))

    # 8 Vasya
    vas = g.rashi in R.VASYA[b.rashi] or b.rashi in R.VASYA[g.rashi]
    items.append(_item("Vasya", MATCH if vas else NO_MATCH,
                       "Rasis are vasya" if vas else "Rasis are not vasya to each other"))

    # 9 Rajju
    br, gr = R.RAJJU[b.nakshatra], R.RAJJU[g.nakshatra]
    items.append(_item("Rajju", NO_MATCH if br == gr else MATCH, f"Boy {br} rajju, girl {gr} rajju"))

    # 10 Vedha
    pair = tuple(sorted((b.nakshatra, g.nakshatra)))
    vedha = pair in {tuple(sorted(p)) for p in R.VEDHA_PAIRS}
    items.append(_item("Vedha", NO_MATCH if vedha else MATCH,
                       f"{NAKSHATRAS[b.nakshatra]} and {NAKSHATRAS[g.nakshatra]}"
                       + (" are vedha" if vedha else " are not vedha")))

    # 11 Varna (by rasi): boy's varna equal to or higher than the girl's
    bv, gv = R.VARNA[b.rashi], R.VARNA[g.rashi]
    items.append(_item("Varna", MATCH if bv >= gv else NO_MATCH,
                       f"Boy {R.VARNA_NAMES[bv]}, girl {R.VARNA_NAMES[gv]}"))

    # 12 Nadi: different nadi matches; same nadi fails unless an exception applies
    bn, gn = R.NADI[b.nakshatra], R.NADI[g.nakshatra]
    nadi_reason = f"Boy {R.NADI_NAMES[bn]} nadi, girl {R.NADI_NAMES[gn]} nadi"
    if bn != gn:
        nadi_item = _item("Nadi", MATCH, nadi_reason)
    else:
        exc = nadi_exception(b, g) if R.PORUTHAM_NADI_EXCEPTIONS else None
        nadi_item = _item("Nadi", MATCH if exc else NO_MATCH,
                          nadi_reason + (f" — same nadi excused: {exc}" if exc else " — same nadi"))
        nadi_item["exception"] = exc
    items.append(nadi_item)

    for it in items:
        it["critical"] = it["name"] in R.PORUTHAM_CRITICAL
        it["keyForUttamam"] = it["name"] in R.PORUTHAM_UTTAMAM_REQUIRED

    total = len(items)
    status = {i["name"]: i["status"] for i in items}
    matched = sum(1 for i in items if i["status"] == MATCH)
    partial = sum(1 for i in items if i["status"] == PARTIAL)
    failed_critical = [i["name"] for i in items if i["critical"] and i["status"] == NO_MATCH]

    def view(accept: set[str], count: int) -> dict:
        ok = lambda names: [n for n in names if status[n] not in accept]  # noqa: E731
        missing = ok(R.PORUTHAM_UTTAMAM_REQUIRED)
        if failed_critical:
            result, label = "REJECTED", "Rejected (" + ", ".join(failed_critical) + ")"
        elif not missing:
            result, label = "UTTAMAM", R.PORUTHAM_LABELS["UTTAMAM"]
        elif not ok(R.PORUTHAM_MADHYAMAM_REQUIRED):
            result, label = "MADHYAMAM", R.PORUTHAM_LABELS["MADHYAMAM"]
        else:
            result, label = "ADHAMAM", R.PORUTHAM_LABELS["ADHAMAM"]
        return {"matched": count, "of": total, "result": result, "label": label, "keyNotMatched": missing}

    strict = view({MATCH}, matched)
    lenient = view({MATCH, PARTIAL}, matched + partial)
    return envelope(
        "PORUTHAM", strict["result"], strict["label"],
        score={"partialCount": partial, "strict": strict, "lenient": lenient},
        details={"items": items, "starCount": star_count, "rasiCount": rasi_count},
    )
