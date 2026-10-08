"""Framework-independent orchestration used by the API (and usable from scripts)."""
from __future__ import annotations

from .core.ayanamsa import Ayanamsa
from .core import dasha as _dasha
from .core import naming as _naming, numerology as _numerology
from .core.chart import Chart, build_chart
from .core.ephemeris.base import PositionMode
from .core.timeutil import InputError, parse_date, parse_time, to_utc
from .geo import get_resolver
from .matching import REGISTRY, Method
from .schemas import ChartImageRequest, ChartRequest, ImagePart, MatchRequest, NamingRequest, PersonIn, Sex


class ResolvedPerson:
    def __init__(self, person: PersonIn, positions: PositionMode | None = None):
        self.person = person
        self.positions = positions
        self.warnings: list[str] = []
        resolver = get_resolver()
        if person.place:
            place, w = resolver.resolve(person.place)
            self.warnings += w
            self.lat, self.lon = place.lat, place.lon
            self.place = place.to_dict()
            tz = place.timezone
            offset = None  # the place's own time zone always wins
            if person.utcOffset:
                self.warnings.append("utcOffset ignored because 'place' was given; the place's time zone was used.")
        else:
            self.lat, self.lon = float(person.lat), float(person.lon)
            self.place = None
            offset = person.utcOffset
            tz = None if offset else resolver.timezone_for(self.lat, self.lon)
        d, t = parse_date(person.dob), parse_time(person.tob)
        self.time = to_utc(d, t, tz, offset)
        self.warnings += self.time.warnings
        self._charts: dict[Ayanamsa, Chart] = {}

    def chart(self, model: Ayanamsa) -> Chart:
        if model not in self._charts:
            self._charts[model] = build_chart(self.time.jd_ut, self.lat, self.lon, model, positions=self.positions)
        return self._charts[model]

    def dasha(self, model: Ayanamsa, as_of=None) -> dict:
        """Vimshottari dasha from the Moon in this chart; dates in the birth place's local time."""
        offset = self.time.local - self.time.utc.replace(tzinfo=None)
        return _dasha.compute(self.chart(model).moon.longitude, self.time.utc, offset, as_of)

    def moon_speed(self, model: Ayanamsa) -> float:
        """Moon's motion in degrees per day at birth (from positions 6 hours either side)."""
        from .core.ephemeris import get_engine
        from .core.ephemeris.base import DEFAULT_POSITION_MODE
        eng, jd = get_engine(), self.time.jd_ut
        mode = self.positions or DEFAULT_POSITION_MODE
        a, b = eng.positions(jd - 0.25, model, mode)["Moon"], eng.positions(jd + 0.25, model, mode)["Moon"]
        return ((b - a) % 360) / 0.5

    def naming(self, model: Ayanamsa, names: list[str] | None = None) -> dict:
        """Birth star and pada with starting syllables, date-of-birth numbers, and an analysis of each name given."""
        star = _naming.birth_star(self.chart(model).moon.longitude, self.moon_speed(model), self.time.local)
        nums = _numerology.numbers_for(self.time.local.date(), star["lord"])
        out = {"birthStar": star, "numbers": nums}
        if names:
            out["names"] = [{**_numerology.analyse(n, nums["birth"], nums["destiny"]),
                             "firstSound": _naming.first_sound(n, star["nakshatraIndex"], star["pada"])}
                            for n in names if n and n.strip()]
        return out

    def summary(self, model: Ayanamsa) -> dict:
        c = self.chart(model).to_dict()
        planets = c.pop("planets")
        warnings = self.warnings + c.pop("warnings")
        return {
            "name": self.person.name,
            "sex": self.person.sex.value,
            "birth": {
                "localTime": self.time.local.isoformat(),
                "utcTime": self.time.utc.isoformat().replace("+00:00", "Z"),
                "utcOffset": self.time.utc_offset,
                "timezone": self.time.timezone,
                "lat": round(self.lat, 5),
                "lon": round(self.lon, 5),
                "resolvedPlace": self.place,
            },
            **c,
            "planets": planets,
            "warnings": warnings,
        }


def run_match(req: MatchRequest) -> dict:
    a, b = ResolvedPerson(req.personA, req.options.positions), ResolvedPerson(req.personB, req.options.positions)
    boy, girl = (a, b) if req.personA.sex == Sex.M else (b, a)
    model = req.options.ayanamsa
    out: dict = {"ayanamsa": model.value, "boy": boy.summary(model), "girl": girl.summary(model)}
    seen = set()
    for m in req.options.methods:
        if m in seen:
            continue
        seen.add(m)
        key, fn, needs_kp = REGISTRY[Method(m)]
        mdl = Ayanamsa.KP if needs_kp else model
        out[key] = fn(boy.chart(mdl), girl.chart(mdl))
    return out


def run_chart(req: ChartRequest) -> dict:
    p = ResolvedPerson(req.person, req.positions)
    return {**p.summary(req.ayanamsa), "dasha": p.dasha(req.ayanamsa)}


def run_naming(req: NamingRequest) -> dict:
    p = ResolvedPerson(req.person)
    return {"ayanamsa": req.ayanamsa.value, **p.naming(req.ayanamsa, req.names), "warnings": p.warnings}


def search_places(q: str, limit: int = 5) -> list[dict]:
    if not q or not q.strip():
        raise InputError("INVALID_PLACE", "Query is empty.")
    return [{**r["place"].to_dict(), "score": r["score"]} for r in get_resolver().search(q, limit)]


def run_chart_image(req: ChartImageRequest) -> str:
    from .matching import kp
    from .render import svg

    p = ResolvedPerson(req.person, req.positions)
    include = [i.value for i in req.include] or [i.value for i in ImagePart]
    chart = p.chart(req.ayanamsa)
    kp_chart = p.chart(Ayanamsa.KP) if "KP_TABLES" in include else None
    sigs = kp.planet_significations(kp_chart) if kp_chart else None
    place = (p.place or {}).get("name") or f"{p.lat:.4f}, {p.lon:.4f}"
    heading = [req.person.name or req.__dict__.get("name") or "",  # legacy field read without deprecation warning
               f"{p.time.local.strftime('%d/%m/%Y %H:%M:%S')}  ({p.time.utc_offset})  ·  {place}"]
    heading = [h for h in heading if h]
    return svg.render(chart, kp_chart, sigs, req.lang.value, include, heading)
