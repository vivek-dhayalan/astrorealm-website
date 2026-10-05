"""Free-text place → coordinates + IANA time zone."""
from __future__ import annotations

import json
import math
import os
import threading
import time
import urllib.parse
import urllib.request

from ..core.timeutil import InputError
from .store import GeoStore, Place, haversine_km, normalize

try:  # optional, faster/better fuzzy matching
    from rapidfuzz import fuzz as _fuzz

    def similarity(a: str, b: str) -> float:
        return float(_fuzz.ratio(a, b))
except ImportError:  # pragma: no cover - exercised where rapidfuzz is absent
    from difflib import SequenceMatcher

    def similarity(a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio() * 100.0

try:
    from timezonefinder import TimezoneFinder  # type: ignore

    _TF = TimezoneFinder()
except ImportError:  # pragma: no cover
    _TF = None

DEFAULT_COUNTRY = os.environ.get("MATCHAPI_DEFAULT_COUNTRY", "IN")
NOMINATIM_ENABLED = os.environ.get("MATCHAPI_NOMINATIM", "1") == "1"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = os.environ.get("MATCHAPI_USER_AGENT", "MatchAPI/0.1 (personal astrology matching API)")

DEFAULT_COUNTRY_BONUS = 6.0  # prefer Indian places when no country is given
MIN_NAME_SIMILARITY = 78
AMBIGUITY_MARGIN = 4.0
SAME_PLACE_KM = 25


class PlaceResolver:
    def __init__(self, store: GeoStore | None):
        self.store = store
        self._nominatim_lock = threading.Lock()
        self._last_call = 0.0

    # ------------------------------------------------------------ scoring
    @staticmethod
    def _parse(query: str) -> tuple[str, list[str]]:
        parts = [normalize(p) for p in query.split(",")]
        parts = [p for p in parts if p]
        if not parts:
            raise InputError("INVALID_PLACE", "Place is empty.")
        return parts[0], parts[1:]

    def search(self, query: str, limit: int = 5) -> list[dict]:
        name, hints = self._parse(query)
        if self.store is None:
            return []
        best: dict[int, dict] = {}
        for matched, place in self.store.candidates(name):
            sim = similarity(name, matched)
            if sim < MIN_NAME_SIMILARITY:
                continue
            score = sim
            country_hinted = False
            hint_hits = 0
            for h in hints:
                if place.admin1 and similarity(h, normalize(place.admin1)) >= 85:
                    score += 12
                    hint_hits += 1
                elif (place.countryName and similarity(h, normalize(place.countryName)) >= 85) or \
                        (place.country and h == place.country.lower()):
                    score += 10
                    hint_hits += 1
                    country_hinted = True
            if hints and not hint_hits:
                score -= 8
            if not country_hinted and place.country == DEFAULT_COUNTRY:
                score += DEFAULT_COUNTRY_BONUS
            score += min(6.0, math.log10(place.population + 1))
            prev = best.get(place.id)
            if prev is None or score > prev["score"]:
                best[place.id] = {"score": round(score, 2), "place": place}
        ranked = sorted(best.values(), key=lambda x: -x["score"])
        return ranked[:limit]

    def resolve(self, query: str) -> tuple[Place, list[str]]:
        warnings: list[str] = []
        ranked = self.search(query, limit=10)
        if ranked:
            top = ranked[0]
            rivals = [r for r in ranked[1:]
                      if top["score"] - r["score"] < AMBIGUITY_MARGIN
                      and haversine_km(top["place"].lat, top["place"].lon, r["place"].lat, r["place"].lon) > SAME_PLACE_KM]
            if rivals:
                raise InputError(
                    "AMBIGUOUS_PLACE",
                    f"'{query}' matches several places; add the state/country or pass lat/lon.",
                    {"candidates": [r["place"].to_dict() for r in [top] + rivals[:4]]},
                )
            return top["place"], warnings
        place = self._nominatim(query)
        if place:
            warnings.append("Place resolved via OpenStreetMap Nominatim (not found in local GeoNames data).")
            return place, warnings
        if self.store is None:
            raise InputError("GEO_DATA_MISSING",
                             "Local GeoNames data is not built (run scripts/build_geonames.py) and online lookup failed.")
        raise InputError("PLACE_NOT_FOUND", f"Could not find '{query}'. Check the spelling or pass lat/lon.")

    # ---------------------------------------------------------- timezone
    def timezone_for(self, lat: float, lon: float) -> str | None:
        if _TF is not None:
            tz = _TF.timezone_at(lat=lat, lng=lon)
            if tz:
                return tz
        if self.store is not None:
            near = self.store.nearest(lat, lon)
            if near:
                return near.timezone
        return None

    # ---------------------------------------------------------- Nominatim
    def _nominatim(self, query: str) -> Place | None:
        if not NOMINATIM_ENABLED:
            return None
        key = "nominatim:" + normalize(query)
        if self.store is not None:
            cached = self.store.cache_get(key)
            if cached is not None:
                return Place(**cached) if cached else None
        url = NOMINATIM_URL + "?" + urllib.parse.urlencode(
            {"q": query, "format": "jsonv2", "limit": 1, "addressdetails": 1})
        try:
            with self._nominatim_lock:
                wait = 1.0 - (time.time() - self._last_call)
                if wait > 0:
                    time.sleep(wait)  # usage policy: max 1 request/second
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                self._last_call = time.time()
        except Exception:  # noqa: BLE001 — offline / blocked → treat as not found
            return None
        place = None
        if data:
            hit = data[0]
            lat, lon = float(hit["lat"]), float(hit["lon"])
            addr = hit.get("address", {})
            place = Place(None, hit.get("name") or query, addr.get("state"),
                          (addr.get("country_code") or "").upper() or None, addr.get("country"),
                          lat, lon, self.timezone_for(lat, lon), 0, "nominatim")
        if self.store is not None:
            self.store.cache_put(key, place.__dict__ if place else None)
        return place


_resolver: PlaceResolver | None = None


def get_resolver() -> PlaceResolver:
    global _resolver
    if _resolver is None:
        try:
            store = GeoStore()
        except FileNotFoundError:
            store = None
        _resolver = PlaceResolver(store)
    return _resolver
