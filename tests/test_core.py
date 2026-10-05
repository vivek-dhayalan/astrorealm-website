from datetime import date, time

import pytest

import app.core.ephemeris.builtin as B
from app.core.ayanamsa import Ayanamsa, ayanamsa_deg
from app.core.chart import house_of
from app.core.reference import NAKSHATRAS, count_inclusive, nakshatra_index, pada, rashi_index, sub_lord
from app.core.timeutil import InputError, julian_day, parse_time, to_utc


# ------------------------------------------------------------------ time
@pytest.mark.parametrize("raw,expected", [
    ("19:45", time(19, 45)), ("07:45 PM", time(19, 45)), ("7:45pm", time(19, 45)),
    ("12:10 AM", time(0, 10)), ("12:10 PM", time(12, 10)), ("7.45 a.m.", time(7, 45)),
    ("23:59:30", time(23, 59, 30)), ("00:00", time(0, 0)),
])
def test_parse_time(raw, expected):
    assert parse_time(raw) == expected


@pytest.mark.parametrize("raw", ["25:00", "13:00 PM", "7 PM", "ab:cd", "10:75"])
def test_parse_time_rejects(raw):
    with pytest.raises(InputError):
        parse_time(raw)


def test_ist_conversion_and_jd():
    r = to_utc(date(2000, 1, 1), time(17, 30), "Asia/Kolkata", None)
    assert r.utc.hour == 12 and r.utc_offset == "+05:30"
    assert r.jd_ut == pytest.approx(2451545.0, abs=1e-9)


def test_wartime_india_offset_from_tzdata():
    r = to_utc(date(1943, 6, 1), time(12, 0), "Asia/Kolkata", None)
    assert r.utc_offset == "+06:30"
    assert any("1956" in w for w in r.warnings)


def test_explicit_offset_wins():
    r = to_utc(date(1950, 1, 1), time(6, 0), "Asia/Kolkata", "+05:21")
    assert (r.utc.hour, r.utc.minute) == (0, 39)


def test_julian_day_meeus_example():
    from datetime import datetime, timezone
    assert julian_day(datetime(1957, 10, 4, 19, 26, 24, tzinfo=timezone.utc)) == pytest.approx(2436116.31, abs=1e-6)


# ------------------------------------------------------------- reference
def test_nakshatra_pada_rashi_boundaries():
    assert NAKSHATRAS[nakshatra_index(0.0)] == "Ashwini"
    assert NAKSHATRAS[nakshatra_index(13.3334)] == "Bharani"
    assert NAKSHATRAS[nakshatra_index(359.99)] == "Revati"
    assert pada(3.33) == 1 and pada(3.34) == 2 and pada(13.32) == 4
    assert rashi_index(29.999) == 0 and rashi_index(30.0) == 1


def test_sub_lords():
    assert sub_lord(0.5) == "Ketu"          # Ashwini first sub (0°–0°46'40")
    assert sub_lord(0.8) == "Venus"
    assert sub_lord(27.0) == "Sun"          # Krittika starts with its own lord
    assert sub_lord(27.5) == "Moon"
    assert sub_lord(13.3333) == "Mercury"  # last sub of Ashwini


def test_count_inclusive():
    assert count_inclusive(0, 0, 27) == 1
    assert count_inclusive(9, 3, 27) == 22
    assert count_inclusive(4, 1, 12) == 10


def test_house_of_wraps():
    cusps = [350 + 30 * i for i in range(12)]
    cusps = [c % 360 for c in cusps]
    assert house_of(355, cusps) == 1 and house_of(5, cusps) == 1 and house_of(21, cusps) == 2


# ------------------------------------------------------------- ephemeris
def test_moon_meeus_47a():
    assert B.moon_longitude_tropical(2448724.5) == pytest.approx(133.162655, abs=2e-5)


def test_venus_meeus_33a():
    # Meeus apparent λ = 313.08102 (includes nutation); Kepler elements agree to < 0.02°
    assert B.planet_longitude_tropical("Venus", 2448976.5) == pytest.approx(313.081, abs=0.02)


def test_sun_meeus_25a():
    assert B.sun_longitude_tropical(2448908.5) == pytest.approx(199.904, abs=0.01)


def test_lahiri_and_kp_ayanamsa_at_j2000():
    assert ayanamsa_deg(2451545.0, Ayanamsa.LAHIRI) == pytest.approx(23.8571, abs=0.002)
    diff = ayanamsa_deg(2451545.0, Ayanamsa.LAHIRI) - ayanamsa_deg(2451545.0, Ayanamsa.KP)
    assert diff == pytest.approx(0.0966, abs=0.003)  # KP ≈ Lahiri − 5'48"


@pytest.mark.parametrize("ramc", [0, 37, 123, 250, 333])
@pytest.mark.parametrize("lat", [8.5, 13.08, 28.6, -33.9, 51.5])
def test_placidus_self_consistency(ramc, lat):
    eps = B.mean_obliquity(2451545.0)
    asc = B.ascendant(ramc, eps, lat)
    for frac, above in ((1.0, True), (1.0, False)):
        c = B._placidus_cusp(ramc, eps, lat, frac, above)
        assert abs(((asc - c + 180) % 360) - 180) < 1e-6
    assert abs(((B.midheaven(ramc, eps) - B._placidus_cusp(ramc, eps, lat, 0.0, True) + 180) % 360) - 180) < 1e-6


def test_equator_ascendant_when_aries_culminates():
    assert B.ascendant(0.0, 23.44, 0.0) == pytest.approx(90.0, abs=1e-9)


def test_cusps_are_ordered():
    _, _, cusps = B.placidus_cusps(2451545.0, 2451545.0007, 13.08, 80.27)
    spans = [(cusps[(i + 1) % 12] - cusps[i]) % 360 for i in range(12)]
    assert all(0 < s < 90 for s in spans) and sum(spans) == pytest.approx(360)


def test_kp_lords_levels():
    from app.core.reference import kp_lords
    # Ashwini 0°: Ketu star, Ketu sub, Ketu sub-sub, Ketu sub-sub-sub
    assert kp_lords(0.0001) == ["Ketu", "Ketu", "Ketu", "Ketu"]
    # A cusp from one of the astrologer's verified printouts: Mithuna 14°48'54"
    assert kp_lords(60 + 14 + 48 / 60 + 54 / 3600) == ["Rahu", "Ketu", "Rahu", "Saturn"]
    import random
    for _ in range(2000):
        x = random.uniform(0, 360)
        assert kp_lords(x, 2)[1] == sub_lord(x)


def test_nutation_magnitude():
    dpsi, deps = B.nutation(2457053.0)  # early 2015
    assert abs(dpsi) * 3600 < 18 and abs(deps) * 3600 < 10
