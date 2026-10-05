from app import service
from app.core.ayanamsa import Ayanamsa
from app.core.chart import build_chart
from app.core.ephemeris.base import PositionMode
from app.core.timeutil import parse_date, parse_time, to_utc
from app.schemas import ChartRequest, MatchRequest

T = to_utc(parse_date("2012-04-18"), parse_time("09:25"), "Asia/Kolkata", None)
LAT, LON = 13 + 4 / 60, 80 + 17 / 60


def _sec(a, b):
    return abs(((a - b + 180) % 360) - 180) * 3600


def test_modes_differ_by_aberration_sized_amounts():
    t = build_chart(T.jd_ut, LAT, LON, Ayanamsa.KP, positions=PositionMode.TRUE)
    a = build_chart(T.jd_ut, LAT, LON, Ayanamsa.KP, positions=PositionMode.APPARENT)
    assert 15 < _sec(t.planets["Sun"].longitude, a.planets["Sun"].longitude) < 25
    assert _sec(t.planets["Moon"].longitude, a.planets["Moon"].longitude) < 2
    assert _sec(t.planets["Rahu"].longitude, a.planets["Rahu"].longitude) < 0.01
    assert t.cusps == a.cusps  # houses do not depend on planet positions


def test_sensitivity_is_reported_when_lords_differ():
    from app.core.reference import kp_lords
    found = None
    for minute in range(0, 24 * 60, 7):  # scan the day until some lord differs between the two modes
        jd = T.jd_ut + minute / 1440
        c = build_chart(jd, LAT, LON, Ayanamsa.KP, positions=PositionMode.TRUE)
        if c.position_sensitive:
            found = (jd, c)
            break
    assert found, "expected at least one position-sensitive lord within a day"
    jd, c = found
    a = build_chart(jd, LAT, LON, Ayanamsa.KP, positions=PositionMode.APPARENT)
    levels = ["star", "sub", "subSub", "subSubSub"]
    for d in c.position_sensitive:
        i = levels.index(d["level"])
        assert kp_lords(c.planets[d["planet"]].longitude)[i] == d["true"]
        assert kp_lords(a.planets[d["planet"]].longitude)[i] == d["apparent"] != d["true"]
    assert any("APPARENT" in w for w in c.warnings)


def test_request_option_is_echoed():
    person = {"sex": "F", "dob": "2012-04-18", "tob": "09:25", "lat": LAT, "lon": LON}
    r = service.run_chart(ChartRequest.model_validate({"person": person, "positions": "APPARENT"}))
    assert r["positions"] == "APPARENT"
    r = service.run_chart(ChartRequest.model_validate({"person": person}))
    assert r["positions"] == "TRUE"
    m = service.run_match(MatchRequest.model_validate({
        "personA": person, "personB": {**person, "sex": "M"},
        "options": {"positions": "APPARENT", "methods": ["KP_7TH_CUSP"]}}))
    assert m["boy"]["positions"] == m["girl"]["positions"] == "APPARENT"
