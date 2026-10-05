import os

import pytest

from app.core.timeutil import InputError
from app.geo import GeoStore, PlaceResolver


@pytest.fixture(scope="module")
def resolver():
    return PlaceResolver(GeoStore(os.environ["MATCHAPI_GEO_DB"]))


def test_exact_city(resolver):
    p, _ = resolver.resolve("Madurai")
    assert p.name == "Madurai" and p.timezone == "Asia/Kolkata"


def test_alternate_name(resolver):
    p, _ = resolver.resolve("Trivandrum")
    assert p.name == "Thiruvananthapuram"


def test_typo_tolerance(resolver):
    p, _ = resolver.resolve("Maduri, Tamil Nadu")
    assert p.name == "Madurai"


def test_indian_default_bias_for_salem(resolver):
    p, _ = resolver.resolve("Salem")
    assert p.country == "IN"


def test_country_hint_overrides_bias(resolver):
    p, _ = resolver.resolve("Salem, Oregon")
    assert p.country == "US" and p.admin1 == "Oregon"


def test_ambiguous_same_country(resolver):
    with pytest.raises(InputError) as e:
        resolver.resolve("Aurangabad")
    assert e.value.code == "AMBIGUOUS_PLACE"
    assert {c["admin1"] for c in e.value.extra["candidates"]} >= {"Maharashtra", "Bihar"}


def test_state_hint_disambiguates(resolver):
    p, _ = resolver.resolve("Aurangabad, Bihar")
    assert p.admin1 == "Bihar"


def test_not_found(resolver):
    with pytest.raises(InputError) as e:
        resolver.resolve("Qwertyuiopville")
    assert e.value.code == "PLACE_NOT_FOUND"


def test_nearest_timezone(resolver):
    assert resolver.store.nearest(9.5, 78.0).timezone == "Asia/Kolkata"
    assert resolver.timezone_for(51.5, -0.1) == "Europe/London"
