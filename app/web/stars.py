"""Reference data for the nakshatra and rasi pages, and star-to-star Porutham computed with the site's own rules.

Porutham depends only on the Moon's nakshatra, rasi and pada, so every pair of padas (108 x 108) can be worked out
in advance. A star pair covers 4 x 4 pada pairs; where they disagree (stars that span two rasis, or the same star)
the result is shown as a range.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from types import SimpleNamespace

from ..core.reference import (NAKSHATRA_LORDS, NAKSHATRA_SPAN, NAKSHATRAS, PADA_SPAN, RASHI_ENGLISH, RASHI_LORDS,
                              RASHIS, rashi_index)
from ..matching import porutham
from ..render import i18n
from ..rules import v1 as R


def slug(name: str) -> str:
    return name.lower().replace(" ", "-")


NAK_SLUGS = [slug(n) for n in NAKSHATRAS]
RASI_SLUGS = [slug(n) for n in RASHIS]
NAK_BY_SLUG = {s: i for i, s in enumerate(NAK_SLUGS)}
RASI_BY_SLUG = {s: i for i, s in enumerate(RASI_SLUGS)}

# Presiding deity and symbol (traditional; Taittiriya Brahmana / common Jyotisha usage)
NAK_DEITY_SYMBOL = [
    ("the Ashwini Kumaras, physicians of the gods", "a horse's head"),
    ("Yama, lord of dharma and death", "the yoni (womb)"),
    ("Agni, the fire god", "a razor or a flame"),
    ("Brahma (Prajapati), the creator", "an ox cart or chariot"),
    ("Soma, the Moon god", "a deer's head"),
    ("Rudra, the storm form of Shiva", "a teardrop or a diamond"),
    ("Aditi, mother of the gods", "a bow and quiver"),
    ("Brihaspati, teacher of the gods", "a cow's udder or a lotus"),
    ("the Nagas, serpent deities", "a coiled serpent"),
    ("the Pitrs, the ancestors", "a royal throne"),
    ("Bhaga, god of fortune and marital happiness", "the front legs of a bed or a hammock"),
    ("Aryaman, god of contracts and friendship", "the back legs of a bed"),
    ("Savitr, the Sun as giver of life", "an open hand"),
    ("Tvashtar (Vishwakarma), the divine architect", "a bright jewel or pearl"),
    ("Vayu, the wind god", "a young shoot swaying in the wind"),
    ("Indra and Agni together", "a triumphal arch or a potter's wheel"),
    ("Mitra, god of friendship", "a lotus"),
    ("Indra, king of the gods", "an earring or an umbrella"),
    ("Nirriti, goddess of dissolution", "a bunch of roots"),
    ("Apas, the waters", "a winnowing fan"),
    ("the Vishvedevas, the universal gods", "an elephant's tusk"),
    ("Vishnu, the preserver", "an ear or three footprints"),
    ("the eight Vasus", "a drum (mridangam)"),
    ("Varuna, lord of the cosmic waters", "an empty circle of a hundred healers"),
    ("Aja Ekapada, the one-footed goat", "a sword or the front of a funeral cot"),
    ("Ahir Budhnya, serpent of the deep", "the back of a funeral cot or twins"),
    ("Pushan, nourisher and protector of travellers", "a fish or a drum"),
]

RASI_SYMBOL = ["a ram", "a bull", "a pair of twins", "a crab", "a lion", "a maiden", "a pair of scales",
               "a scorpion", "a bow (archer)", "a crocodile (sea-goat)", "a water pot", "a pair of fish"]
RASI_ELEMENT = ["Fire", "Earth", "Air", "Water"] * 3
RASI_QUALITY = ["Movable (chara)", "Fixed (sthira)", "Dual (dwiswabhava)"] * 4
EXALTED = {0: "Sun", 1: "Moon", 9: "Mars", 5: "Mercury", 3: "Jupiter", 11: "Venus", 6: "Saturn"}
DEBILITATED = {6: "Sun", 7: "Moon", 3: "Mars", 11: "Mercury", 9: "Jupiter", 5: "Venus", 0: "Saturn"}

GRADE_ORDER = ["UTTAMAM", "MADHYAMAM", "ADHAMAM", "REJECTED"]
GRADE_LABEL = {"UTTAMAM": "Uttamam (excellent)", "MADHYAMAM": "Madhyamam (average)", "ADHAMAM": "Adhamam (poor)",
               "REJECTED": "Rejected"}


def dms(deg: float) -> str:
    d = int(deg + 1e-9)
    m = round((deg - d) * 60)
    if m == 60:
        d, m = d + 1, 0
    return f"{d}°{m:02d}′"


@dataclass(frozen=True)
class Pada:
    index: int        # 0..107
    nakshatra: int
    pada: int         # 1..4
    rashi: int


PADAS = [Pada(p, p // 4, p % 4 + 1, rashi_index(p * PADA_SPAN + PADA_SPAN / 2)) for p in range(108)]


def nak_rasis(n: int) -> list[tuple[int, list[int]]]:
    """[(rashi, [padas])] for a nakshatra."""
    out: dict[int, list[int]] = {}
    for p in PADAS[n * 4:n * 4 + 4]:
        out.setdefault(p.rashi, []).append(p.pada)
    return list(out.items())


def rasi_naks(r: int) -> list[tuple[int, list[int]]]:
    """[(nakshatra, [padas])] falling in a rasi."""
    out: dict[int, list[int]] = {}
    for p in PADAS:
        if p.rashi == r:
            out.setdefault(p.nakshatra, []).append(p.pada)
    return list(out.items())


def _chart(p: Pada):
    return SimpleNamespace(moon=SimpleNamespace(nakshatra=p.nakshatra, rashi=p.rashi, pada=p.pada))


@dataclass(frozen=True)
class PairSummary:
    """Strict Porutham for a bride's star (girl) and a groom's star (boy), across their padas."""
    lo: int
    hi: int
    of: int
    grades: tuple[str, ...]  # distinct grades, best first

    @property
    def always(self) -> str | None:
        return self.grades[0] if len(self.grades) == 1 else None

    @property
    def count_text(self) -> str:
        return str(self.lo) if self.lo == self.hi else f"{self.lo}–{self.hi}"


@lru_cache(maxsize=1)
def star_table() -> list[list[PairSummary]]:
    """table[girl_star][boy_star]"""
    table = []
    for gn in range(27):
        row = []
        for bn in range(27):
            counts, grades = [], set()
            for gp in PADAS[gn * 4:gn * 4 + 4]:
                for bp in PADAS[bn * 4:bn * 4 + 4]:
                    res = porutham.match(_chart(bp), _chart(gp))
                    counts.append(res["score"]["strict"]["matched"])
                    grades.add(res["result"])
                    of = res["score"]["strict"]["of"]
            row.append(PairSummary(min(counts), max(counts), of,
                                   tuple(g for g in GRADE_ORDER if g in grades)))
        table.append(row)
    return table


def matches_for(n: int, as_bride: bool) -> dict[str, list[int]]:
    """Stars of the other partner grouped by outcome: 'best' (always Uttamam), 'some' (Uttamam for some padas),
    'avoid' (always rejected)."""
    t = star_table()
    out = {"best": [], "some": [], "avoid": []}
    for other in range(27):
        cell = t[n][other] if as_bride else t[other][n]
        if cell.always == "UTTAMAM":
            out["best"].append(other)
        elif "UTTAMAM" in cell.grades:
            out["some"].append(other)
        elif cell.always == "REJECTED":
            out["avoid"].append(other)
    return out


def vedha_partners(n: int) -> list[int]:
    return sorted({b if a == n else a for a, b in R.VEDHA_PAIRS if n in (a, b)})


def names(lang: str, kind: str, i: int) -> str:
    key = NAKSHATRAS[i] if kind == "nakshatra" else RASHIS[i]
    return i18n.get(lang)[kind][key]


def nak_facts(n: int) -> dict:
    start = n * NAKSHATRA_SPAN
    yoni, gender = R.YONI[n]
    return {
        "name": NAKSHATRAS[n], "ta": names("ta", "nakshatra", n), "hi": names("hi", "nakshatra", n),
        "lord": NAKSHATRA_LORDS[n], "start": start, "end": start + NAKSHATRA_SPAN,
        "rasis": nak_rasis(n), "deity": NAK_DEITY_SYMBOL[n][0], "symbol": NAK_DEITY_SYMBOL[n][1],
        "gana": R.GANA_NAMES[R.GANA[n]], "yoni": f"{yoni} ({'male' if gender == 'M' else 'female'})",
        "nadi": R.NADI_NAMES[R.NADI[n]], "rajju": R.RAJJU[n], "vedha": vedha_partners(n),
    }


def rasi_facts(r: int) -> dict:
    vasya = sorted(R.VASYA[r] | {o for o, s in R.VASYA.items() if r in s})
    vs = R.VASHYA_BY_RASHI[r]
    vashya = " / ".join(R.VASHYA_NAMES[v] for v in vs) if isinstance(vs, tuple) else R.VASHYA_NAMES[vs]
    return {
        "name": RASHIS[r], "english": RASHI_ENGLISH[r], "ta": names("ta", "rashi", r), "hi": names("hi", "rashi", r),
        "lord": RASHI_LORDS[r], "start": r * 30.0, "symbol": RASI_SYMBOL[r], "element": RASI_ELEMENT[r],
        "quality": RASI_QUALITY[r], "exalted": EXALTED.get(r), "debilitated": DEBILITATED.get(r),
        "naks": rasi_naks(r), "varna": R.VARNA_NAMES[R.VARNA[r]], "vashya": vashya, "vasya": vasya,
        "rasi_good": sorted((r + c - 1) % 12 for c in R.RASI_MATCH_COUNTS),
        "bhakoot_bad": sorted((r + k) % 12 for k in (1, 11, 4, 8, 5, 7)),
    }
