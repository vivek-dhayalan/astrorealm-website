from __future__ import annotations

from ..rules import v1 as R


def relation(a: str, b: str) -> str:
    """How planet a regards planet b: 'friend' | 'neutral' | 'enemy' | 'same'."""
    if a == b:
        return "same"
    if b in R.FRIENDS.get(a, set()):
        return "friend"
    if b in R.ENEMIES.get(a, set()):
        return "enemy"
    return "neutral"


def band(value: float, bands: list[tuple]) -> tuple[str, str]:
    for minimum, result, label in bands:
        if value >= minimum:
            return result, label
    return bands[-1][1], bands[-1][2]


def envelope(method: str, result: str, label: str, details: dict, score: dict | None = None,
             warnings: list[str] | None = None) -> dict:
    out = {"method": method, "rulesVersion": R.VERSION, "result": result, "label": label}
    if score is not None:
        out["score"] = score
    out["details"] = details
    out["warnings"] = warnings or []
    return out


def nadi_exception(b, g) -> str | None:
    """Reason a same-nadi pair is excused, or None. b/g are the Moon PlanetPos of boy/girl."""
    if b.nakshatra == g.nakshatra and b.rashi != g.rashi:
        return "Same nakshatra but different rashi"
    if b.nakshatra == g.nakshatra and b.pada != g.pada:
        return "Same nakshatra but different pada"
    if b.rashi == g.rashi and b.nakshatra != g.nakshatra:
        return "Same rashi but different nakshatra"
    return None
