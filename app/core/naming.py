"""Baby naming: the Moon's nakshatra pada, its starting syllables in each script, and a name's first-sound check.

Syllable tables are in app.rules.v1 (Latin, Devanagari, Tamil); Telugu, Kannada and Malayalam are produced from the
Devanagari by the Unicode block offset (the Brahmi-derived blocks share one layout for these letters).
"""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta

from ..rules import v1 as R
from .reference import NAKSHATRA_LORDS, NAKSHATRA_SPAN, NAKSHATRAS, PADA_SPAN, RASHIS, nakshatra_index, norm360

SCRIPTS = ("latin", "dev", "ta", "te", "kn", "ml")
LANG_SCRIPT = {"en": "latin", "hi": "dev", "ta": "ta", "te": "te", "kn": "kn", "ml": "ml"}
_BLOCK = {"te": 0x0C00, "kn": 0x0C80, "ml": 0x0D00}


def from_devanagari(text: str, script: str) -> str:
    base = _BLOCK[script]
    return "".join(chr(ord(c) - 0x0900 + base) if 0x0900 <= ord(c) <= 0x097F else c for c in text)


def _table(script: str) -> list:
    if script == "latin":
        return R.PADA_SYLLABLES
    if script == "dev":
        return R.PADA_DEVANAGARI
    if script == "ta":
        return R.PADA_TAMIL
    return [[[from_devanagari(s, script) for s in pada] for pada in nak] for nak in R.PADA_DEVANAGARI]


def syllables(nak: int, pada: int, script: str = "latin") -> list[str]:
    """Syllables for one pada (1-4): the common one first, then the variants; duplicates dropped."""
    out: list[str] = []
    for s in _table(script)[nak][pada - 1]:
        if s not in out:
            out.append(s)
    return out


def star_syllables(nak: int) -> dict[str, list[list[str]]]:
    """All four padas of a nakshatra in every script."""
    return {sc: [syllables(nak, p, sc) for p in (1, 2, 3, 4)] for sc in SCRIPTS}


def birth_star(moon_longitude: float, moon_speed: float, birth_local: datetime) -> dict:
    """Moon's nakshatra and pada, when that pada began and ends (birth-place local time), and a boundary flag.

    moon_speed: degrees per day at birth (about 12–15).
    """
    lon = norm360(moon_longitude)
    nak = nakshatra_index(lon)
    within = lon - nak * NAKSHATRA_SPAN
    pada = int(within // PADA_SPAN) + 1
    into = within - (pada - 1) * PADA_SPAN           # degrees since the pada began
    left = PADA_SPAN - into                           # degrees until it ends
    days = lambda deg: timedelta(days=deg / moon_speed)  # noqa: E731
    start, end = birth_local - days(into), birth_local + days(left)
    minutes = min(into, left) / moon_speed * 1440
    return {
        "nakshatra": NAKSHATRAS[nak], "nakshatraIndex": nak, "pada": pada, "lord": NAKSHATRA_LORDS[nak],
        "rashi": RASHIS[int(lon // 30)], "padaStart": start.isoformat(timespec="minutes"),
        "padaEnd": end.isoformat(timespec="minutes"), "minutesToEdge": round(minutes),
        "nearBoundary": minutes < R.NAMING_BOUNDARY_WARN_MIN,
        "otherPada": (pada - 1 if into < left else pada + 1),   # the pada a small time error would give (0/5 = next star)
        "syllables": star_syllables(nak),
    }


# ------------------------------------------------------------------ first-sound check
_VOWELS = "aeiou"
_VOWEL_FORMS = {  # how a syllable's vowel is commonly spelt in English
    "a": ("aa", "a"), "i": ("ee", "ii", "i", "y"), "u": ("oo", "uu", "u"), "e": ("ai", "ay", "e"), "o": ("au", "ow", "o"),
}


def _base(cons: str) -> str:
    """Spelling-insensitive consonant: aspiration dropped (Tha ≈ Ta, Dh ≈ D, Chh ≈ Ch), w ≈ v, f ≈ ph; sh kept."""
    c = cons.replace("w", "v").replace("f", "ph")
    if c in ("sh", "ch"):
        return c
    if len(c) > 1 and c.endswith("h"):
        c = c[:-1]
    return c


def _split(s: str) -> tuple[str, str]:
    s = s.lower()
    i = next((k for k, ch in enumerate(s) if ch in _VOWELS), len(s))
    return s[:i], s[i:]


def _latin_match(name: str, syllable: str) -> bool:
    cons, vowel = _split(syllable)
    n = "".join(ch for ch in unicodedata.normalize("NFKD", name.lower()) if "a" <= ch <= "z")
    ncons, rest = _split(n)
    want = _base(cons)
    # a conjunct counts by its first consonant: Pra- ≈ Pa, Shre- ≈ She, Kri- ≈ Ki
    heads = {_base(ncons)} | ({_base(ncons[:-1])} if len(ncons) > 1 and ncons[-1] in "rylv" else set())
    if want not in heads or not rest:
        return False
    for form in _VOWEL_FORMS[vowel[0] if vowel else "a"]:
        if rest.startswith(form):
            nxt = rest[len(form):len(form) + 1]
            if form == "a" and nxt in ("i", "u", "y"):   # 'ai'/'au' are e/o sounds, not a
                return False
            if form == "e" and nxt == "e":               # 'ee' is a long i
                return False
            if form == "o" and nxt == "o":               # 'oo' is a long u
                return False
            return True
    return False


def script_of(text: str) -> str:
    for ch in text:
        o = ord(ch)
        if 0x0900 <= o <= 0x097F:
            return "dev"
        if 0x0B80 <= o <= 0x0BFF:
            return "ta"
        for sc, base in _BLOCK.items():
            if base <= o < base + 0x80:
                return sc
        if ch.isalpha():
            return "latin"
    return "latin"


def first_sound(name: str, nak: int, pada: int) -> dict:
    """PADA: starts with a syllable of the birth pada · STAR: of another pada of the same star · NONE."""
    name = (name or "").strip()
    sc = script_of(name)
    check = (lambda s: _latin_match(name, s)) if sc == "latin" else (lambda s: name.startswith(s))
    order = [pada] + [p for p in (1, 2, 3, 4) if p != pada]
    for p in order:
        for s in syllables(nak, p, sc):
            if check(s):
                return {"result": "PADA" if p == pada else "STAR", "pada": p, "syllable": s, "script": sc}
    return {"result": "NONE", "pada": None, "syllable": None, "script": sc}
