"""Birth-time parsing, local→UTC conversion, Julian Day and ΔT."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class InputError(ValueError):
    """Raised for invalid user input; carries a machine-readable code."""

    def __init__(self, code: str, message: str, extra: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.extra = extra or {}


_TIME_RE = re.compile(
    r"^\s*(?P<h>\d{1,2})[:.](?P<m>\d{2})(?:[:.](?P<s>\d{2}))?\s*(?P<ampm>[AaPp]\.?\s*[Mm]\.?)?\s*$"
)


def parse_time(value: str) -> time:
    """Accepts '19:45', '19:45:30', '7:45 PM', '07:45pm', '7.45 a.m.'.
    Without AM/PM the value is read as 24-hour time."""
    m = _TIME_RE.match(value or "")
    if not m:
        raise InputError("INVALID_TIME", f"Unrecognised time '{value}'. Use 'HH:MM' (24h) or 'hh:mm AM/PM'.")
    h, mi, s = int(m["h"]), int(m["m"]), int(m["s"] or 0)
    ampm = m["ampm"]
    if mi > 59 or s > 59:
        raise InputError("INVALID_TIME", f"Minutes/seconds out of range in '{value}'.")
    if ampm:
        if not 1 <= h <= 12:
            raise InputError("INVALID_TIME", f"12-hour time must have hour 1-12: '{value}'.")
        pm = ampm.strip().lower().startswith("p")
        h = (h % 12) + (12 if pm else 0)
    elif h > 23:
        raise InputError("INVALID_TIME", f"Hour out of range in '{value}'.")
    return time(h, mi, s)


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value.strip())
    except Exception as exc:  # noqa: BLE001
        raise InputError("INVALID_DATE", f"Date must be YYYY-MM-DD, got '{value}'.") from exc


_OFFSET_RE = re.compile(r"^([+-])(\d{1,2}):?(\d{2})$")


def parse_offset(value: str) -> timedelta:
    m = _OFFSET_RE.match(value.strip())
    if not m:
        raise InputError("INVALID_UTC_OFFSET", f"utcOffset must look like '+05:30', got '{value}'.")
    sign = 1 if m.group(1) == "+" else -1
    hours, minutes = int(m.group(2)), int(m.group(3))
    if hours > 14 or minutes > 59:
        raise InputError("INVALID_UTC_OFFSET", f"utcOffset out of range: '{value}'.")
    return sign * timedelta(hours=hours, minutes=minutes)


@dataclass
class ResolvedTime:
    local: datetime
    utc: datetime
    utc_offset: str
    timezone: str | None
    jd_ut: float
    warnings: list[str] = field(default_factory=list)


def _fmt_offset(td: timedelta) -> str:
    total = int(td.total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{sign}{h:02d}:{m:02d}" + (f":{s:02d}" if s else "")


def to_utc(d: date, t: time, tz_name: str | None, utc_offset: str | None) -> ResolvedTime:
    local = datetime.combine(d, t)
    warnings: list[str] = []
    if utc_offset:
        off = parse_offset(utc_offset)
        utc = (local - off).replace(tzinfo=timezone.utc)
        tz_label = tz_name
    else:
        if not tz_name:
            raise InputError("TIMEZONE_UNRESOLVED", "Could not determine the time zone; pass utcOffset (e.g. '+05:30').")
        try:
            zi = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError as exc:
            raise InputError("TIMEZONE_UNRESOLVED", f"Unknown time zone '{tz_name}'. Install 'tzdata' or pass utcOffset.") from exc
        aware = local.replace(tzinfo=zi, fold=0)
        # Detect DST gaps / overlaps
        roundtrip = aware.astimezone(timezone.utc).astimezone(zi).replace(tzinfo=None)
        if roundtrip != local:
            warnings.append("Birth time falls in a daylight-saving gap for this zone; time shifted by tzdata rules.")
        if local.replace(tzinfo=zi, fold=0).utcoffset() != local.replace(tzinfo=zi, fold=1).utcoffset():
            warnings.append("Birth time is ambiguous (daylight-saving overlap); the earlier offset was used.")
        off = aware.utcoffset()
        utc = aware.astimezone(timezone.utc)
        tz_label = tz_name
        if tz_name in ("Asia/Kolkata", "Asia/Calcutta") and d.year < 1956:
            warnings.append(
                "Births in India before 1956 may have been recorded in local time (Bombay/Calcutta/Madras time) "
                "rather than IST; confirm the offset or pass utcOffset."
            )
    return ResolvedTime(
        local=local,
        utc=utc,
        utc_offset=_fmt_offset(off),
        timezone=tz_label,
        jd_ut=julian_day(utc),
        warnings=warnings,
    )


def julian_day(dt_utc: datetime) -> float:
    """Julian Day (UT) for a UTC datetime, proleptic Gregorian."""
    y, m = dt_utc.year, dt_utc.month
    day = dt_utc.day + (dt_utc.hour + (dt_utc.minute + (dt_utc.second + dt_utc.microsecond / 1e6) / 60.0) / 60.0) / 24.0
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + day + b - 1524.5


def delta_t_seconds(jd_ut: float) -> float:
    """ΔT = TT − UT (Espenak & Meeus polynomial fits)."""
    y = 2000.0 + (jd_ut - 2451545.0) / 365.25
    if 1900 <= y < 1920:
        t = y - 1900
        return -2.79 + 1.494119 * t - 0.0598939 * t**2 + 0.0061966 * t**3 - 0.000197 * t**4
    if 1920 <= y < 1941:
        t = y - 1920
        return 21.20 + 0.84493 * t - 0.076100 * t**2 + 0.0020936 * t**3
    if 1941 <= y < 1961:
        t = y - 1950
        return 29.07 + 0.407 * t - t**2 / 233 + t**3 / 2547
    if 1961 <= y < 1986:
        t = y - 1975
        return 45.45 + 1.067 * t - t**2 / 260 - t**3 / 718
    if 1986 <= y < 2005:
        t = y - 2000
        return 63.86 + 0.3345 * t - 0.060374 * t**2 + 0.0017275 * t**3 + 0.000651814 * t**4 + 0.00002373599 * t**5
    if 2005 <= y < 2050:
        t = y - 2000
        return 62.92 + 0.32217 * t + 0.005589 * t**2
    u = (y - 1820) / 100
    return -20 + 32 * u * u
