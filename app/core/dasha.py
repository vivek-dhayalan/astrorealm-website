"""Vimshottari dasha: mahadasha, bhukti (antardasha) and antara (pratyantardasha) periods.

The Moon's nakshatra at birth picks the first mahadasha lord; the part of the nakshatra the Moon has
already crossed is the part of that dasha already "used up" before birth. Each period splits into nine
sub-periods in the same order and proportions (starting with its own lord) — the same rule that gives
the KP sub lords along the zodiac.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from ..rules import v1 as R
from .reference import NAKSHATRA_LORDS, NAKSHATRA_SPAN, VIMSHOTTARI, VIMSHOTTARI_TOTAL, nakshatra_index, norm360

YEARS = dict(VIMSHOTTARI)
ORDER = [lord for lord, _ in VIMSHOTTARI]


@dataclass
class Period:
    lord: str
    start: datetime  # UTC
    end: datetime    # UTC

    def contains(self, when: datetime) -> bool:
        return self.start <= when < self.end


def _span(years: float) -> timedelta:
    return timedelta(days=years * R.DASHA_YEAR_DAYS)


def _sequence(first: str) -> list[str]:
    i = ORDER.index(first)
    return ORDER[i:] + ORDER[:i]


def sub_periods(parent: Period) -> list[Period]:
    """The nine sub-periods of a period, starting with its own lord, in Vimshottari proportions."""
    total = parent.end - parent.start
    out, start = [], parent.start
    for lord in _sequence(parent.lord):
        end = start + total * YEARS[lord] / VIMSHOTTARI_TOTAL
        out.append(Period(lord, start, end))
        start = end
    out[-1].end = parent.end  # no rounding drift
    return out


def mahadashas(moon_longitude: float, birth_utc: datetime) -> tuple[list[Period], float]:
    """The nine mahadashas of one full cycle, from the (pre-birth) start of the birth dasha.

    Returns (periods, fraction of the first dasha already elapsed at birth).
    """
    lon = norm360(moon_longitude)
    first = NAKSHATRA_LORDS[nakshatra_index(lon)]
    elapsed = (lon % NAKSHATRA_SPAN) / NAKSHATRA_SPAN
    start = birth_utc - _span(YEARS[first] * elapsed)
    out = []
    for lord in _sequence(first):
        end = start + _span(YEARS[lord])
        out.append(Period(lord, start, end))
        start = end
    return out, elapsed


def _add_months(d: date, months: int) -> date:
    y, m = divmod(d.month - 1 + months, 12)
    y, m = d.year + y, m + 1
    last = (date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1)).day
    return date(y, m, min(d.day, last))


def ymd(start: date, end: date) -> tuple[int, int, int]:
    """Calendar difference in years, months and days (end ≥ start; month ends clamp, e.g. 31 Jan + 1 m = 28 Feb)."""
    months = (end.year - start.year) * 12 + end.month - start.month
    if _add_months(start, months) > end:
        months -= 1
    days = (end - _add_months(start, months)).days
    return months // 12, months % 12, days


def years_ymd(years: float) -> tuple[int, int, int]:
    """Years as astrologers write a dasha balance: whole years, then 12 months of 30 days."""
    y = int(years)
    months = (years - y) * 12
    m = int(months)
    d = round((months - m) * 30)
    if d == 30:
        m, d = m + 1, 0
    if m == 12:
        y, m = y + 1, 0
    return y, m, d


def _local(dt: datetime, offset: timedelta) -> date:
    return (dt + offset).date()


def compute(moon_longitude: float, birth_utc: datetime, utc_offset: timedelta = timedelta(0),
            as_of: datetime | None = None) -> dict:
    """Everything the pages need: balance at birth, the current periods, and the transition tables.

    Dates are given in the birth place's local time (utc_offset); as_of defaults to now.
    """
    if birth_utc.tzinfo is None:
        birth_utc = birth_utc.replace(tzinfo=timezone.utc)
    now = as_of or datetime.now(timezone.utc)
    mds, elapsed = mahadashas(moon_longitude, birth_utc)
    loc = lambda dt: _local(dt, utc_offset)  # noqa: E731
    first = mds[0]

    stamp = lambda dt: (dt + utc_offset).replace(tzinfo=None).isoformat(timespec="seconds")  # noqa: E731

    def row(p: Period) -> dict:
        return {"lord": p.lord, "start": loc(p.start).isoformat(), "end": loc(p.end).isoformat(),
                "startAt": stamp(p.start), "endAt": stamp(p.end),
                "days": round((p.end - p.start).total_seconds() / 86400, 2)}

    def with_remaining(p: Period) -> dict:
        return {**row(p), "remaining": list(ymd(loc(now), loc(p.end))),
                "daysLeft": round((p.end - now).total_seconds() / 86400, 1)}

    current = None
    bhuktis: list[Period] = []
    antaras: list[Period] = []
    sookshmas: list[Period] = []
    md = next((p for p in mds if p.contains(now)), None)
    if md and now >= birth_utc:
        bhuktis = sub_periods(md)
        bh = next(p for p in bhuktis if p.contains(now))
        antaras = sub_periods(bh)
        an = next(p for p in antaras if p.contains(now))
        sookshmas = sub_periods(an)
        sk = next(p for p in sookshmas if p.contains(now))
        current = {"mahadasha": with_remaining(md), "bhukti": with_remaining(bh), "antara": with_remaining(an),
                   "sookshma": with_remaining(sk)}
    return {
        "system": "VIMSHOTTARI",
        "yearDays": R.DASHA_YEAR_DAYS,
        "asOf": loc(now).isoformat(),
        "birthBalance": {"lord": first.lord, "ymd": list(years_ymd(YEARS[first.lord] * (1 - elapsed))),
                         "years": round(YEARS[first.lord] * (1 - elapsed), 4), "end": loc(first.end).isoformat()},
        "current": current,
        # the first dasha is shown from birth (its earlier part ran before birth)
        "mahadashas": [{**row(mds[0]), "start": loc(birth_utc).isoformat()}] + [row(p) for p in mds[1:]],
        "bhuktis": [row(p) for p in bhuktis],
        "antaras": [row(p) for p in antaras],      # of the current bhukti
        "sookshmas": [row(p) for p in sookshmas],  # of the current antara
    }
