"""Builds a tiny GeoNames DB from fixtures and points the app at it."""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

_tmp = Path(tempfile.mkdtemp(prefix="matchapi-test-"))
os.environ["MATCHAPI_GEO_DB"] = str(_tmp / "geonames.sqlite")
os.environ["MATCHAPI_NOMINATIM"] = "0"

from app.geo.store import GeoStore  # noqa: E402
from build_geonames import ingest, load_admin1, load_countries  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "geonames"


def _build_fixture_db() -> None:
    store = GeoStore(os.environ["MATCHAPI_GEO_DB"], create=True)
    admin1 = load_admin1(FIX / "admin1CodesASCII.txt")
    countries = load_countries(FIX / "countryInfo.txt")
    seen: set[int] = set()
    for f in ("IN.txt", "cities500.txt"):
        ingest(store, FIX / f, admin1, countries, seen)
    store.finalize({"attribution": "test"})


_build_fixture_db()
