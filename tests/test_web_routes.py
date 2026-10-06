"""Website routes end to end (needs FastAPI + httpx)."""
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.web import routes  # noqa: E402
from app.web.settings import Settings  # noqa: E402

client = TestClient(app)

BIRTH = {"name": "Test Person", "sex": "M", "dob": "1987-08-12", "tob": "06:10", "place": "Trichy",
         "lat": "10.8155", "lon": "78.69651", "lang": "en", "ayanamsa": "LAHIRI", "parts": ["RASI", "NAVAMSA"]}


@pytest.fixture(autouse=True)
def fresh_limiter():
    routes._limiter = None
    yield
    routes._limiter = None


@pytest.mark.parametrize("path", ["/", "/horoscope", "/match", "/credits", "/privacy", "/terms", "/learn", "/upcoming", "/ta", "/hi", "/ta/learn/porutham", "/hi/learn/ashtakoota", "/ta/match",
                                  "/hi/learn/nakshatra/rohini", "/ta/learn/nakshatra-porutham-table",
                                  "/learn/nakshatras", "/learn/rasis", "/learn/nakshatra-porutham-table",
                                  "/learn/nakshatra/rohini", "/learn/rasi/mesha", "/horoscope?lang=ta",
                                  "/learn/ayanamsa", "/learn/porutham", "/sitemap.xml",
                                  "/static/site.css", "/static/site.js"])
def test_pages_load(path):
    assert client.get(path).status_code == 200


def test_horoscope_generates_and_is_not_cached():
    r = client.post("/horoscope", data=BIRTH)
    assert r.status_code == 200
    assert "Test Person" in r.text and "<svg" in r.text and "Navamsa" in r.text
    assert r.headers["cache-control"] == "no-store"


def test_horoscope_errors_are_shown():
    r = client.post("/horoscope", data={**BIRTH, "dob": ""})
    assert r.status_code == 422 and "Please enter the date of birth" in r.text


def test_match_bride_left():
    data = {"b_name": "Bride One", "b_dob": "1996-07-14", "b_tob": "06:20", "b_place": "Coimbatore",
            "b_lat": "11.00555", "b_lon": "76.96612", "g_name": "Groom One", "g_dob": "1993-11-02",
            "g_tob": "21:05", "g_place": "Puducherry", "g_lat": "11.93381", "g_lon": "79.82979",
            "lang": "en", "ayanamsa": "KP"}
    r = client.post("/match", data=data)
    assert r.status_code == 200
    assert r.text.index("Bride One") < r.text.index("Groom One")


def test_place_text_only_is_resolved():
    r = client.post("/horoscope", data={**BIRTH, "lat": "", "lon": "", "place": "Madurai"})
    assert r.status_code == 200 and "Madurai" in r.text


def test_nearest_place():
    r = client.get("/v1/places/nearest", params={"lat": 13.08, "lon": 80.27})
    assert r.status_code == 200 and r.json()["nearest"]["name"] == "Chennai"


def test_rate_limit(monkeypatch):
    monkeypatch.setattr(routes, "_limiter", routes.RateLimiter(2))
    codes = [client.post("/horoscope", data=BIRTH).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


def test_turnstile_enforced(monkeypatch):
    s = Settings(turnstile_site_key="site", turnstile_secret="secret")
    monkeypatch.setattr(routes, "get_settings", lambda: s)

    async def deny(secret, token, ip):
        return token == "good"

    monkeypatch.setattr(routes, "verify_turnstile", deny)
    assert client.post("/horoscope", data=BIRTH).status_code == 400
    assert client.post("/horoscope", data={**BIRTH, "cf-turnstile-response": "good"}).status_code == 200


def test_ads_txt(monkeypatch):
    assert client.get("/ads.txt").status_code == 404
    monkeypatch.setattr(routes, "get_settings", lambda: Settings(adsense_client="ca-pub-123"))
    r = client.get("/ads.txt")
    assert r.status_code == 200 and r.text.strip() == "google.com, pub-123, DIRECT, f08c47fec0942fa0"


def test_unknown_guide_404():
    assert client.get("/learn/nope").status_code == 404


def test_old_hindi_url_redirects():
    r = client.get("/hi/learn/guna-milan", follow_redirects=False)
    assert r.status_code == 301 and r.headers["location"] == "/hi/learn/ashtakoota"


def test_language_pages_and_404():
    assert "ஜாதகம்" in client.get("/ta/horoscope").text
    assert client.get("/ta/learn/no-such-guide").status_code == 404
    assert client.get("/ta/learn/nakshatra/no-such-star").status_code == 404
