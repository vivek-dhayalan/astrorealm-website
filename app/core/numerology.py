"""Name numerology: Chaldean (Cheiro), Pythagorean and the pyramid method, plus the date-of-birth numbers.

Pure functions; the tables live in app.rules.v1. The website runs the same arithmetic in site.js as the user
types (static/site.js `numerology`), and tests/test_naming.py keeps the two in step.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date

from ..rules import v1 as R

_LETTERS = re.compile(r"[A-Z]")


def digit_sum(n: int) -> int:
    return sum(int(c) for c in str(abs(n)))


def reduce(n: int, keep_master: bool = False) -> int:
    """Add the digits until one digit is left (11, 22, 33 stay when keep_master)."""
    while n > 9 and not (keep_master and n in R.MASTER_NUMBERS):
        n = digit_sum(n)
    return n


def letters(name: str) -> list[str]:
    """The English letters of a name, upper case; accents dropped, spaces/dots/digits ignored."""
    plain = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode().upper()
    return _LETTERS.findall(plain)


def chaldean(name: str) -> dict:
    vals = [(c, R.CHALDEAN[c]) for c in letters(name)]
    total = sum(v for _, v in vals)
    return {"letters": vals, "total": total, "number": reduce(total)}


def pythagorean(name: str) -> dict:
    vals = [(c, R.PYTHAGOREAN[c]) for c in letters(name)]
    total = sum(v for _, v in vals)
    number = reduce(total, keep_master=True)
    return {"letters": vals, "total": total, "number": number, "digit": reduce(number)}


def pyramid(values: list[int]) -> dict:
    """Add neighbours row by row (sums above 9 reduced to one digit) down to the apex."""
    rows = [list(values)]
    while len(rows[-1]) > 1:
        r = rows[-1]
        rows.append([reduce(a + b) for a, b in zip(r, r[1:])])
    return {"rows": rows, "apex": rows[-1][0] if values else None}


def birth_number(d: date) -> int:
    """Mulank / psychic number: the day of the month reduced."""
    return reduce(d.day)


def destiny_number(d: date) -> int:
    """Bhagyank / life-path number: every digit of the date reduced."""
    return reduce(digit_sum(int(d.strftime("%d%m%Y"))))


def _planet(n: int) -> str:
    p = R.NUMBER_PLANET[reduce(n)]
    return R.NODE_PROXY.get(p, p)


def relation(a: int, b: int) -> str:
    """How number a's planet regards number b's planet: same | friend | neutral | enemy."""
    pa, pb = _planet(a), _planet(b)
    if pa == pb:
        return "same"
    if pb in R.FRIENDS.get(pa, set()):
        return "friend"
    if pb in R.ENEMIES.get(pa, set()):
        return "enemy"
    return "neutral"


def friendly(n: int) -> set[int]:
    return {k for k in range(1, 10) if relation(n, k) in ("same", "friend")}


def harmony_numbers(birth: int, destiny: int) -> list[int]:
    """Numbers whose planet is the birth number's own or its friend, and not an enemy of the destiny number's planet.

    The birth number leads (the usual practice); the destiny number only rules numbers out.
    """
    return sorted(k for k in friendly(birth) if relation(destiny, k) != "enemy")


def verdict(n: int, birth: int, destiny: int) -> str:
    """HARMONY (a harmony number) | AVOID (an enemy of the birth or destiny number) | NEUTRAL."""
    n = reduce(n)
    if n in harmony_numbers(birth, destiny):
        return "HARMONY"
    if "enemy" in (relation(birth, n), relation(destiny, n)):
        return "AVOID"
    return "NEUTRAL"


def numbers_for(d: date, nakshatra_lord: str | None = None) -> dict:
    b, dn = birth_number(d), destiny_number(d)
    out = {"birth": b, "birthPlanet": R.NUMBER_PLANET[b], "destiny": dn, "destinyPlanet": R.NUMBER_PLANET[dn],
           "harmony": harmony_numbers(b, dn)}
    if nakshatra_lord:
        out["nakshatraLord"] = nakshatra_lord
        out["nakshatraNumber"] = next(k for k, p in R.NUMBER_PLANET.items() if p == nakshatra_lord)
    return out


def analyse(name: str, birth: int, destiny: int) -> dict:
    """Every method for one name, with a harmony verdict on each method's single digit."""
    ch, py = chaldean(name), pythagorean(name)
    pyr = pyramid([v for _, v in ch["letters"]])
    out = {"name": name, "chaldean": ch, "pythagorean": py, "pyramid": pyr}
    if ch["letters"]:
        out["verdicts"] = {"chaldean": verdict(ch["number"], birth, destiny),
                           "pythagorean": verdict(py["digit"], birth, destiny),
                           "pyramid": verdict(pyr["apex"], birth, destiny)}
    return out
