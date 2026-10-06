import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

import app.geo.resolver as resolver_mod  # noqa: E402
from app.main import app  # noqa: E402

resolver_mod._resolver = None  # pick up the fixture DB
client = TestClient(app)

BOY = {"sex": "M", "dob": "1991-09-23", "tob": "06:30 AM", "lat": 13.0827, "lon": 80.2707}
GIRL = {"sex": "F", "dob": "1992-11-02", "tob": "21:10", "place": "Madurai, Tamil Nadu"}


def test_match_all_methods():
    r = client.post("/v1/match", json={"personA": BOY, "personB": GIRL})
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) >= {"boy", "girl", "ashtakoota", "porutham", "manglik", "rahuKetu", "kp7thCusp"}
    assert body["girl"]["birth"]["resolvedPlace"]["name"] == "Madurai"
    assert body["boy"]["birth"]["timezone"] == "Asia/Kolkata"
    assert body["porutham"]["score"]["strict"]["of"] == 12


def test_selected_methods_only():
    r = client.post("/v1/match", json={"personA": GIRL, "personB": BOY, "options": {"methods": ["ASHTAKOOTA"]}})
    assert r.status_code == 200
    body = r.json()
    assert "ashtakoota" in body and "porutham" not in body
    assert body["boy"]["sex"] == "M"  # order of persons does not matter


def test_same_sex_rejected():
    r = client.post("/v1/match", json={"personA": BOY, "personB": {**GIRL, "sex": "M"}})
    assert r.status_code == 422


def test_place_and_coords_together_rejected():
    r = client.post("/v1/chart", json={"person": {**BOY, "place": "Chennai"}})
    assert r.status_code == 422


def test_ambiguous_place_returns_candidates():
    r = client.post("/v1/chart", json={"person": {**GIRL, "place": "Aurangabad"}})
    assert r.status_code == 422
    assert r.json()["error"] == "AMBIGUOUS_PLACE" and len(r.json()["candidates"]) >= 2


def test_places_endpoint():
    r = client.get("/v1/places", params={"q": "Salem"})
    assert r.status_code == 200 and r.json()["candidates"][0]["country"] == "IN"


def test_bad_time():
    r = client.post("/v1/chart", json={"person": {**BOY, "tob": "13:00 PM"}})
    assert r.status_code == 422 and r.json()["error"] == "INVALID_TIME"


def test_utc_offset_ignored_with_place():
    r = client.post("/v1/chart", json={"person": {**GIRL, "utcOffset": "+00:00"}})
    assert r.status_code == 200
    assert r.json()["birth"]["utcOffset"] == "+05:30"
    assert any("utcOffset ignored" in w for w in r.json()["warnings"])


def test_swagger_placeholder_offset_is_ignored():
    r = client.post("/v1/chart", json={"person": {**BOY, "utcOffset": "string"}})
    assert r.status_code == 200 and r.json()["birth"]["utcOffset"] == "+05:30"


def test_chart_image_endpoint():
    r = client.post("/v1/chart/image", json={"person": BOY, "lang": "ta"})
    assert r.status_code == 200 and r.headers["content-type"].startswith("image/svg+xml")
    assert r.text.startswith("<svg")


def test_name_is_echoed_and_optional():
    r = client.post("/v1/match", json={"personA": {**BOY, "name": "Arun"}, "personB": GIRL,
                                       "options": {"methods": ["ASHTAKOOTA"]}})
    assert r.status_code == 200
    assert r.json()["boy"]["name"] == "Arun" and r.json()["girl"]["name"] is None
