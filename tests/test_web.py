"""Website: sanitizer, forms, labels, rendering order, rate limit (no FastAPI needed)."""
from app.render import i18n
from app.service import ResolvedPerson
from app.matching import ashtakoota, porutham
from app.render import svg
from app.web import strings, views
from app.web.forms import HoroscopeForm, MatchForm, parse_body
from app.web.sanitize import clean_html
from app.web.security import RateLimiter
from app.web.settings import Settings


def test_sanitizer_keeps_formatting_and_drops_scripts():
    out = clean_html('<p onclick="x()">Hi <b>there</b><script>alert(1)</script></p><img src=x onerror=alert(1)>'
                     '<a href="javascript:alert(1)">link</a><div>line</div><style>p{}</style>')
    assert "<script" not in out and "alert" not in out and "onclick" not in out and "<img" not in out
    assert "<b>there</b>" in out and "link" in out and "<p>line</p>" in out


def test_sanitizer_escapes_text_and_limits_length():
    assert clean_html("<b>a &lt;b&gt; c</b>") == "<b>a &lt;b&gt; c</b>"
    assert len(clean_html("x" * 50_000)) <= 4000
    assert clean_html("<p><br></p>") == ""
    assert clean_html("தமிழ் <i>ತೆಲುಗು</i>") == "தமிழ் <i>ತೆಲುಗು</i>"


def test_every_label_in_every_language():
    for key in strings.keys():
        row = strings._T[key]
        assert len(row) == len(strings.LANGS) and all(row), key
    for lang in strings.LANGS:
        L = i18n.get(lang)
        assert i18n.LANGUAGES[lang] is L
        assert len(L["nakshatra"]) == 27 and len(L["rashi"]) == 12 and len(L["planet_short"]) == 9


def _hform(**over):
    f = {"name": ["Test"], "sex": ["F"], "dob": ["1996-07-14"], "tob": ["06:20"], "place": ["Chennai"],
         "lat": ["13.08784"], "lon": ["80.27847"], "lang": ["ta"], "ayanamsa": ["KP"], "parts": ["RASI", "NAVAMSA"]}
    f.update(over)
    return f


def test_horoscope_form_validation():
    assert not HoroscopeForm.parse(_hform()).errors
    e = HoroscopeForm.parse(_hform(name=[""], dob=["1995-02-30"], tob=["25"], parts=[],
                                   brothers=["1"], brothers_married=["2"], lat=[""], lon=[""], place=[""])).errors
    assert set(e) >= {"name", "dob", "tob", "parts", "brothers", "place"}
    frm = HoroscopeForm.parse(_hform(lang=["xx"], ayanamsa=["nope"], father=["maybe"]))
    assert frm.lang == "en" and frm.ayanamsa.value == "LAHIRI" and frm.father == ""
    frm = HoroscopeForm.parse(_hform(gothram=["Bharadwaja"], mathulam=["Kashyapa" * 10]))
    assert not frm.errors and frm.gothram == "Bharadwaja" and len(frm.mathulam) == 40


def test_parse_body_limits():
    assert parse_body(b"a=1&b=%E0%AE%A4")["b"] == ["த"]
    try:
        parse_body(b"x" * (70 * 1024))
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def _match_html(lang="en"):
    f = {"b_name": ["Bride<script>"], "b_dob": ["1996-07-14"], "b_tob": ["06:20"], "b_place": ["Coimbatore"],
         "b_lat": ["11.00555"], "b_lon": ["76.96612"], "g_name": ["Groom"], "g_dob": ["1993-11-02"],
         "g_tob": ["21:05"], "g_place": ["Puducherry"], "g_lat": ["11.93381"], "g_lon": ["79.82979"],
         "lang": [lang], "ayanamsa": ["KP"]}
    frm = MatchForm.parse(f)
    assert not frm.errors
    people = {"bride": ResolvedPerson(frm.bride.to_person()), "groom": ResolvedPerson(frm.groom.to_person())}
    charts = {r: p.chart(frm.ayanamsa) for r, p in people.items()}
    svgs = {r: svg.grid_svg(c, lang, "RASI", degrees=False) for r, c in charts.items()}
    a = ashtakoota.match(charts["groom"], charts["bride"])
    p = porutham.match(charts["groom"], charts["bride"])
    return views.match_result(Settings(), frm, {"bride": "Coimbatore", "groom": "Puducherry"}, charts, svgs, a, p)


def test_match_page_puts_bride_left_and_escapes_names():
    html = _match_html()
    assert html.index('class="who person bride"') < html.index('class="who person groom"')
    assert html.index('class="chart bride"') < html.index('class="chart groom"')
    # one shared grid: both charts come after all detail rows, so they start on the same line
    assert html.index('class="chart bride"') > html.rindex('class="k g"')
    assert "Bride&lt;script&gt;" in html and "<script>alert" not in html
    assert "Ashtakoota" in html and "Porutham" in html
    assert "KP_7TH" not in html and "Manglik" not in html


def test_match_page_localized():
    html = _match_html("ta")
    assert "மணமகள்" in html and "மணமகன்" in html and "அஷ்டகூட" in html


def test_rate_limiter():
    rl = RateLimiter(3)
    assert all(rl.allow("ip", now=t) for t in (0, 1, 2))
    assert not rl.allow("ip", now=3)
    assert rl.allow("other", now=3)
    assert rl.allow("ip", now=61)


def test_ads_and_turnstile_markup_follow_settings():
    s = Settings(adsense_client="ca-pub-1", adsense_slot_top="111", turnstile_site_key="k", turnstile_secret="x")
    page = views.horoscope_form(s, HoroscopeForm())
    assert 'data-ad-slot="111"' in page and "cf-turnstile" in page and "turnstile/v0/api.js" in page
    off = views.horoscope_form(Settings(production=True), HoroscopeForm())
    assert "adsbygoogle" not in off and "Ad space" not in off


def test_result_pages_have_no_ads_and_generic_titles():
    s = Settings(adsense_client="ca-pub-1", adsense_slot_top="111", adsense_slot_bottom="222")
    frm = MatchForm.parse({"b_name": ["Asha"], "b_dob": ["1996-07-14"], "b_tob": ["06:20"], "b_lat": ["11.00555"],
                           "b_lon": ["76.96612"], "g_name": ["Ravi"], "g_dob": ["1993-11-02"], "g_tob": ["21:05"],
                           "g_lat": ["11.9"], "g_lon": ["79.8"], "lang": ["en"], "ayanamsa": ["KP"]})
    people = {"bride": ResolvedPerson(frm.bride.to_person()), "groom": ResolvedPerson(frm.groom.to_person())}
    charts = {r: p.chart(frm.ayanamsa) for r, p in people.items()}
    svgs = {r: svg.grid_svg(c, "en", "RASI", degrees=False) for r, c in charts.items()}
    html = views.match_result(s, frm, {"bride": "x", "groom": "y"}, charts, svgs,
                              ashtakoota.match(charts["groom"], charts["bride"]),
                              porutham.match(charts["groom"], charts["bride"]))
    assert "adsbygoogle" not in html and "<title>Matching result" in html
    title = html[html.index("<title>"):html.index("</title>")]
    assert "Asha" not in title and "Ravi" not in title
    assert "adsbygoogle" in views.match_form(s, MatchForm())  # forms still carry ads


def test_learn_pages_and_internal_links():
    import re
    from app.web.learn import ARTICLES, BY_SLUG
    s = Settings()
    assert len(ARTICLES) >= 6 and all(a.slug in views.learn_index(s) for a in ARTICLES)
    known = {"/", "/horoscope", "/match", "/learn", "/credits", "/privacy", "/terms"} | {f"/learn/{a.slug}" for a in ARTICLES}
    for a in ARTICLES:
        page = views.learn_article(s, a)
        assert a.title in page
        for href in re.findall(r'href="(/[^"]*)"', a.body):
            assert href in known, (a.slug, href)
    for key, (_, _, href) in views.TIPS.items():
        assert href.removeprefix("/learn/") in BY_SLUG, key


def test_tooltips_on_forms():
    s = Settings()
    h = views.horoscope_form(s, HoroscopeForm())
    for tid in ("tip-ayanamsa", "tip-rasi", "tip-navamsa", "tip-kp_tables"):
        assert f'id="{tid}"' in h
    m = views.match_form(s, MatchForm())
    assert 'id="tip-ayanamsa"' in m and "tip-rasi" not in m


def test_kp_tables_portrait():
    from app.matching import kp
    from tests.helpers import make_chart
    c = make_chart(100.0)
    out = svg.kp_svg(c, kp.planet_significations(c), "ta", compact=True)
    w, h = (float(x) for x in out.split('viewBox="0 0 ')[1].split('"')[0].split())
    wide = svg.kp_svg(c, kp.planet_significations(c), "ta")
    ww, wh = (float(x) for x in wide.split('viewBox="0 0 ')[1].split('"')[0].split())
    # portrait A5 printable area is ~128 x 175 mm once header/footer are allowed for: need h/w >= ~0.9
    assert w < ww and h / w > 0.9 > wh / ww


def test_google_analytics_only_on_public_pages():
    s = Settings(ga_measurement_id="G-ABC123XYZ")
    form = views.horoscope_form(s, HoroscopeForm())
    assert "googletagmanager.com/gtag/js?id=G-ABC123XYZ" in form and "'consent','default'" in form
    assert "Google Analytics" in form  # consent notice
    assert "googletagmanager" in views.learn_index(s)
    html = _match_html()  # result page (built with default settings) — and with GA on:
    assert "googletagmanager" not in html
    frm = MatchForm.parse({"b_name": ["A"], "b_dob": ["1996-07-14"], "b_tob": ["06:20"], "b_lat": ["11.00555"],
                           "b_lon": ["76.96612"], "g_name": ["B"], "g_dob": ["1993-11-02"], "g_tob": ["21:05"],
                           "g_lat": ["11.93381"], "g_lon": ["79.82979"], "lang": ["en"], "ayanamsa": ["KP"]})
    people = {"bride": ResolvedPerson(frm.bride.to_person()), "groom": ResolvedPerson(frm.groom.to_person())}
    charts = {r: p.chart(frm.ayanamsa) for r, p in people.items()}
    svgs = {r: svg.grid_svg(c, "en", "RASI", degrees=False) for r, c in charts.items()}
    res = views.match_result(s, frm, {"bride": "x", "groom": "y"}, charts, svgs,
                             ashtakoota.match(charts["groom"], charts["bride"]),
                             porutham.match(charts["groom"], charts["bride"]))
    assert "googletagmanager" not in res


def test_bad_measurement_id_is_ignored():
    s = Settings(ga_measurement_id="G-1');alert(1);//")
    assert not s.analytics_enabled and "googletagmanager" not in views.home(s)


def test_privacy_lists_only_enabled_services():
    off = views.privacy(Settings())
    assert "AdSense" not in off and "Google Analytics" not in off
    on = views.privacy(Settings(adsense_client="ca-pub-1", ga_measurement_id="G-ABC1234"))
    assert "Google AdSense" in on and "Google Analytics" in on


def test_no_ad_space_without_adsense():
    for s in (Settings(), Settings(production=True)):
        page = views.horoscope_form(s, HoroscopeForm())
        assert 'class="ad ' not in page and "with-side" not in page
    on = views.horoscope_form(Settings(adsense_client="ca-pub-1", adsense_slot_top="1", adsense_slot_side="2"),
                              HoroscopeForm())
    assert "ad-top" in on and "with-side" in on
