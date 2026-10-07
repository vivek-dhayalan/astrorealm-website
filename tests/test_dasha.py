"""Vimshottari dasha calculator."""
from datetime import datetime, timedelta, timezone

from app.core import dasha as D
from app.core.reference import NAKSHATRA_SPAN, sub_lord
from app.rules import v1 as R

BIRTH = datetime(2000, 1, 1, tzinfo=timezone.utc)
YEAR = timedelta(days=R.DASHA_YEAR_DAYS)


def test_balance_at_birth_follows_the_moons_nakshatra():
    assert D.compute(0.0, BIRTH, as_of=BIRTH)["birthBalance"]["lord"] == "Ketu"
    b = D.compute(0.0, BIRTH, as_of=BIRTH)["birthBalance"]
    assert b["years"] == 7 and b["ymd"] == [7, 0, 0]  # start of Ashwini: the whole Ketu dasha is ahead
    half_bharani = NAKSHATRA_SPAN * 1.5
    b = D.compute(half_bharani, BIRTH, as_of=BIRTH)["birthBalance"]
    assert b["lord"] == "Venus" and abs(b["years"] - 10) < 1e-9 and b["ymd"] == [10, 0, 0]


def test_cycle_is_120_years_and_subperiods_add_up():
    mds, elapsed = D.mahadashas(NAKSHATRA_SPAN * 1.5, BIRTH)
    assert [p.lord for p in mds] == ["Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu"]
    assert abs((mds[-1].end - mds[0].start) - 120 * YEAR) < timedelta(seconds=1)
    assert abs(mds[0].start - (BIRTH - 10 * YEAR)) < timedelta(seconds=1)
    bh = D.sub_periods(mds[0])
    assert bh[0].lord == "Venus" and abs((bh[0].end - bh[0].start) - 20 * 20 / 120 * YEAR) < timedelta(seconds=1)
    assert bh[0].start == mds[0].start and bh[-1].end == mds[0].end
    assert all(a.end == b.start for a, b in zip(bh, bh[1:]))


def test_bhukti_proportions_match_kp_sub_lords():
    # the KP sub lords across a nakshatra follow the same order and proportions as the bhuktis of a dasha
    start = 0.0  # Ashwini, Ketu star
    bh = D.sub_periods(D.Period("Ketu", BIRTH, BIRTH + 120 * YEAR))  # scale: 1 year ↔ NAKSHATRA_SPAN/120
    pos = start
    for p in bh:
        width = (p.end - p.start) / YEAR / 120 * NAKSHATRA_SPAN
        assert sub_lord(pos + width / 2) == p.lord
        pos += width


def test_current_periods_and_remaining():
    as_of = datetime(2026, 10, 7, tzinfo=timezone.utc)
    r = D.compute(0.0, BIRTH, timedelta(hours=5, minutes=30), as_of=as_of)
    cur = r["current"]
    assert cur["mahadasha"]["lord"] == "Venus"  # Ketu 7 y, then Venus 20 y
    assert cur["mahadasha"]["start"] <= r["asOf"] < cur["mahadasha"]["end"]
    assert cur["bhukti"]["start"] <= r["asOf"] < cur["bhukti"]["end"]
    assert cur["antara"]["start"] <= r["asOf"] < cur["antara"]["end"]
    assert len(r["mahadashas"]) == 9 and r["mahadashas"][0]["start"] == "2000-01-01"  # first listed from birth
    assert [b["lord"] for b in r["bhuktis"]][0] == "Venus" and len(r["bhuktis"]) == 9
    assert D.compute(0.0, BIRTH, as_of=BIRTH - YEAR)["current"] is None  # before birth


def test_ymd():
    from datetime import date
    assert D.ymd(date(2026, 10, 7), date(2026, 12, 31)) == (0, 2, 24)
    assert D.ymd(date(2020, 1, 31), date(2021, 3, 1)) == (1, 1, 1)
    assert D.years_ymd(12.2575) == (12, 3, 3) and D.years_ymd(0.99999) == (1, 0, 0)


def test_antara_and_sookshma_levels():
    as_of = datetime(2026, 10, 7, tzinfo=timezone.utc)
    r = D.compute(0.0, BIRTH, as_of=as_of)
    cur = r["current"]
    assert len(r["antaras"]) == 9 and len(r["sookshmas"]) == 9
    assert r["antaras"][0]["lord"] == cur["bhukti"]["lord"] and r["sookshmas"][0]["lord"] == cur["antara"]["lord"]
    assert r["sookshmas"][0]["startAt"] == cur["antara"]["startAt"] and r["sookshmas"][-1]["endAt"] == cur["antara"]["endAt"]
    assert cur["sookshma"]["startAt"] <= "2026-10-07T00:00:00" < cur["sookshma"]["endAt"]
    assert abs(sum(x["days"] for x in r["sookshmas"]) - cur["antara"]["days"]) < 0.05
