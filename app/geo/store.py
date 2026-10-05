"""SQLite store for GeoNames places, name index and geocode cache."""
from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import threading
import time
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_DB = Path(os.environ.get("MATCHAPI_GEO_DB", Path(__file__).resolve().parents[2] / "data" / "geonames.sqlite"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS places (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    admin1 TEXT,
    country TEXT,
    country_name TEXT,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    tz TEXT,
    population INTEGER DEFAULT 0,
    feature_code TEXT
);
CREATE TABLE IF NOT EXISTS names (
    norm TEXT NOT NULL,
    place_id INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS geocode_cache (
    query TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    ts REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
"""
INDEXES = """
CREATE INDEX IF NOT EXISTS ix_names_norm ON names(norm);
CREATE INDEX IF NOT EXISTS ix_names_place ON names(place_id);
CREATE INDEX IF NOT EXISTS ix_places_lat ON places(lat);
"""

_PUNCT = re.compile(r"[^a-z0-9 ]+")
_SPACES = re.compile(r"\s+")


def normalize(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii").lower()
    t = _PUNCT.sub(" ", t)
    return _SPACES.sub(" ", t).strip()


@dataclass
class Place:
    id: int | None
    name: str
    admin1: str | None
    country: str | None
    countryName: str | None
    lat: float
    lon: float
    timezone: str | None
    population: int
    source: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("id")
        return d


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 12742 * math.asin(math.sqrt(a))


class GeoStore:
    def __init__(self, path: str | Path = DEFAULT_DB, create: bool = False):
        self.path = Path(path)
        if not create and not self.path.exists():
            raise FileNotFoundError(str(self.path))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        if create:
            self.conn.executescript(SCHEMA)

    @property
    def conn(self) -> sqlite3.Connection:
        c = getattr(self._local, "conn", None)
        if c is None:
            c = sqlite3.connect(str(self.path), check_same_thread=False)
            c.row_factory = sqlite3.Row
            c.executescript(SCHEMA)
            self._local.conn = c
        return c

    # ---------------------------------------------------------------- build
    def insert_places(self, rows: list[tuple], names: list[tuple]) -> None:
        self.conn.executemany(
            "INSERT OR REPLACE INTO places(id,name,admin1,country,country_name,lat,lon,tz,population,feature_code)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
        self.conn.executemany("INSERT INTO names(norm, place_id) VALUES (?,?)", names)

    def finalize(self, meta: dict) -> None:
        self.conn.executescript(INDEXES)
        self.conn.executemany("INSERT OR REPLACE INTO meta(key,value) VALUES (?,?)", list(meta.items()))
        self.conn.commit()

    # --------------------------------------------------------------- lookup
    @staticmethod
    def _place(row: sqlite3.Row, source: str = "geonames") -> Place:
        return Place(row["id"], row["name"], row["admin1"], row["country"], row["country_name"],
                     row["lat"], row["lon"], row["tz"], row["population"] or 0, source)

    def candidates(self, norm_name: str, limit: int = 4000) -> list[tuple[str, Place]]:
        """(matched name, place) pairs for exact and prefix matches of the name."""
        if not norm_name:
            return []
        prefix = norm_name[: max(3, min(5, len(norm_name) - 1))] if len(norm_name) > 3 else norm_name
        rows = self.conn.execute(
            """SELECT n.norm AS matched, p.* FROM names n JOIN places p ON p.id = n.place_id
               WHERE n.norm >= ? AND n.norm < ? ORDER BY p.population DESC LIMIT ?""",
            (prefix, prefix + "\x7f", limit),
        ).fetchall()
        return [(r["matched"], self._place(r)) for r in rows]

    def nearest(self, lat: float, lon: float, max_km: float = 150) -> Place | None:
        for box in (0.5, 1.5, 3.0):
            rows = self.conn.execute(
                "SELECT * FROM places WHERE lat BETWEEN ? AND ? AND lon BETWEEN ? AND ? AND tz IS NOT NULL",
                (lat - box, lat + box, lon - box, lon + box),
            ).fetchall()
            if rows:
                best = min(rows, key=lambda r: haversine_km(lat, lon, r["lat"], r["lon"]))
                if haversine_km(lat, lon, best["lat"], best["lon"]) <= max_km:
                    return self._place(best)
        return None

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM places").fetchone()[0]

    # ---------------------------------------------------------------- cache
    def cache_get(self, key: str):
        row = self.conn.execute("SELECT payload FROM geocode_cache WHERE query=?", (key,)).fetchone()
        return json.loads(row["payload"]) if row else None

    def cache_put(self, key: str, payload) -> None:
        self.conn.execute("INSERT OR REPLACE INTO geocode_cache(query,payload,ts) VALUES (?,?,?)",
                          (key, json.dumps(payload), time.time()))
        self.conn.commit()
