"""Baby naming: pada syllables, first-sound check and name numerology."""
from datetime import date, datetime

import pytest

from app.core import naming as N
from app.core import numerology as NU
from app.core.ayanamsa import Ayanamsa
from app.core.reference import PADA_SPAN
from app.rules import v1 as R
from app.schemas import PersonIn
from app.service import ResolvedPerson


# ------------------------------------------------------------------ numerology
def test_chaldean_table_is_cheiro():
    assert R.CHALDEAN["C"] == 3            # the research draft had C = 2
    assert set(R.CHALDEAN.values()) == set(range(1, 9))   # no letter is 9
    assert len(R.CHALDEAN) == 26


@pytest.mark.parametrize("name, total, number", [("AARAV", 11, 2), ("Charan", 17, 8), ("Lakshmi", 19, 1),
                                                 ("a. arav", 11, 2)])
def test_chaldean_totals(name, total, number):
    r = NU.chaldean(name)
    assert (r["total"], r["number"]) == (total, number)


def test_pythagorean_and_master_numbers():
    assert NU.pythagorean("AARAV")["number"] == 7          # 1+1+9+1+4 = 16
    r = NU.pythagorean("KK")                               # 2+2 = 4
    assert r["number"] == 4
    r = NU.pythagorean("BI")                               # 2+9 = 11 is kept
    assert (r["total"], r["number"], r["digit"]) == (11, 11, 2)


def test_pyramid_worked_example():
    r = NU.pyramid([1, 1, 2, 1, 6])
    assert r["rows"] == [[1, 1, 2, 1, 6], [2, 3, 3, 7], [5, 6, 1], [2, 7], [9]]
    assert r["apex"] == 9
    assert NU.pyramid([v for _, v in NU.chaldean("CHARAN")["letters"]])["apex"] == 5


def test_pyramid_apex_is_binomial_digital_root():
    from math import comb
    for name in ("Aarav", "Charan", "Meenakshi", "Vivek", "Ramanathan"):
        vals = [v for _, v in NU.chaldean(name)["letters"]]
        n = len(vals) - 1
        weighted = sum(comb(n, i) * v for i, v in enumerate(vals))
        assert NU.pyramid(vals)["apex"] == NU.reduce(weighted)


def test_birth_and_destiny_numbers():
    d = date(1990, 8, 23)
    assert NU.birth_number(d) == 5 and NU.destiny_number(d) == 5
    assert NU.birth_number(date(2024, 3, 12)) == 3 and NU.destiny_number(date(2024, 3, 12)) == 5


def test_harmony_numbers():
    # 3 = Jupiter (friends Sun, Moon, Mars); 5 = Mercury rules out the Moon (its enemy)
    assert NU.harmony_numbers(3, 5) == [1, 3, 7, 9]
    for b in range(1, 10):
        for d in range(1, 10):
            assert NU.harmony_numbers(b, d), (b, d)     # never empty
    assert NU.verdict(10, 3, 5) == "HARMONY"             # 10 → 1
    assert NU.verdict(2, 3, 5) == "AVOID"                # Moon is Mercury's enemy
    assert NU.verdict(5, 3, 5) == "AVOID"                # Mercury is Jupiter's enemy
    assert NU.verdict(4, 3, 5) == "NEUTRAL"              # Rahu (as Saturn): neutral to both


def test_analyse_without_english_letters():
    r = NU.analyse("சுரேஷ்", 3, 5)
    assert r["chaldean"]["total"] == 0 and "verdicts" not in r


# ------------------------------------------------------------------ syllables
def test_tables_line_up():
    for t in (R.PADA_DEVANAGARI, R.PADA_TAMIL):
        assert [[len(c) for c in r] for r in t] == [[len(c) for c in r] for r in R.PADA_SYLLABLES]


def test_variants_listed_and_other_scripts():
    assert N.syllables(5, 4) == ["Chha", "Na"]           # Ardra pada 4
    assert N.syllables(21, 4) == ["Kha", "Gha", "Kho"]   # Shravana pada 4
    assert N.syllables(21, 4, "ta") == ["க", "கோ"]       # duplicates dropped
    assert N.syllables(0, 1, "te") == ["చూ"] and N.syllables(0, 1, "kn") == ["ಚೂ"] and N.syllables(0, 1, "ml") == ["ചൂ"]


@pytest.mark.parametrize("name, syllable, expected", [
    ("Lakshmi", "La", True), ("Laila", "La", False), ("Leela", "Li", True), ("Thilak", "Ti", True),
    ("Prakash", "Pa", True), ("Aishwarya", "E", True), ("Arun", "A", True), ("Falguni", "Pha", True),
    ("Dhruv", "Du", True), ("Moorthy", "Mu", True), ("Mohan", "Mo", True), ("Meena", "Mo", False),
])
def test_latin_first_sound(name, syllable, expected):
    assert N._latin_match(name, syllable) is expected


def test_first_sound_levels():
    # Revati (26): De, Do, Cha, Chi
    assert N.first_sound("Devika", 26, 1)["result"] == "PADA"
    assert N.first_sound("Charan", 26, 1) == {"result": "STAR", "pada": 3, "syllable": "Cha", "script": "latin"}
    assert N.first_sound("Arun", 26, 1)["result"] == "NONE"
    assert N.first_sound("தேவி", 26, 1)["result"] == "PADA"
    assert N.first_sound("देविका", 26, 1)["result"] == "PADA"


def test_birth_star_window_and_boundary():
    when = datetime(2024, 1, 1, 12, 0)
    s = N.birth_star(0.1, 13.2, when)                    # 0.1° into Ashwini pada 1
    assert (s["nakshatra"], s["pada"], s["lord"]) == ("Ashwini", 1, "Ketu")
    assert s["nearBoundary"] and s["minutesToEdge"] == round(0.1 / 13.2 * 1440)
    s = N.birth_star(PADA_SPAN * 1.5, 13.2, when)        # middle of pada 2
    assert s["pada"] == 2 and not s["nearBoundary"]
    assert s["syllables"]["latin"][1] == ["Che"]


def test_service_naming():
    p = ResolvedPerson(PersonIn(name="x", sex="F", dob="2024-03-12", tob="06:42", lat=10.8, lon=78.69,
                                utcOffset="+05:30"))
    r = p.naming(Ayanamsa.LAHIRI, ["Charan", " "])
    assert r["birthStar"]["nakshatra"] == "Revati" and r["birthStar"]["pada"] == 2
    assert 11 < p.moon_speed(Ayanamsa.LAHIRI) < 16
    assert r["numbers"]["birth"] == 3 and r["numbers"]["destiny"] == 5 and r["numbers"]["nakshatraNumber"] == 5
    assert len(r["names"]) == 1 and r["names"][0]["firstSound"]["result"] == "STAR"


# ------------------------------------------------------------------ website
def test_naming_text_complete():
    from app.web import naming_text
    from app.web.strings import LANGS
    for k in naming_text.keys():
        row = naming_text._T[k]
        assert len(row) == len(LANGS) and all(row), k
        for text in row:   # same placeholders in every language
            assert sorted(set(__import__("re").findall(r"\{(\w+)\}", text))) == \
                sorted(set(__import__("re").findall(r"\{(\w+)\}", row[0]))), (k, text)


def _naming_form():
    from app.web.forms import NamingForm
    return NamingForm.parse({"dob": ["2024-03-12"], "tob": ["06:42"], "place": ["Trichy"], "lat": ["10.8"],
                             "lon": ["78.69"]})


@pytest.mark.parametrize("lang", ["en", "ta", "hi", "te", "ml", "kn"])
def test_naming_pages(lang):
    import json
    from app.web import views
    from app.web.forms import NamingForm
    from app.web.naming_text import nt
    from app.web.settings import Settings
    form = views.naming_form(Settings(), NamingForm(), ui=lang)
    assert 'action="/baby-names"' in form and 'data-live="/baby-names/part"' in form
    assert 'name="name"' not in form and 'name="sex"' not in form and '<option value="LAHIRI" selected>' in form
    # before the details: the birth-star card holds a hint and the letters, numbers and checker wait (hidden)
    assert __import__("html").escape(nt(lang, "fill_hint")) in form
    assert 'id="nm-results" class="nm-results" aria-live="polite" hidden' in form and 'id="nm-try" hidden' in form
    assert json.loads(form.split('id="naming-data">')[1].split("</script>")[0])["data"] is None
    assert 'href="/baby-names"' in views.home(Settings(), "en")
    frm = _naming_form()
    assert not frm.errors and frm.birth.name == ""
    data = ResolvedPerson(frm.birth.to_person()).naming(frm.ayanamsa)
    html = views.naming_result(Settings(), frm, "Trichy", data, ui=lang)
    assert __import__("html").escape(nt(lang, "h1")) in html and 'id="nm-names"' in html and "/static/naming.js" in html
    boot = json.loads(html.split('<script type="application/json" id="naming-data">')[1].split("</script>")[0])
    payload = boot["data"]
    assert payload["pada"] == 2 and payload["chaldean"]["C"] == 3 and len(payload["verdicts"]) == 9
    assert set(payload["syllables"]) == set(N.SCRIPTS) and boot["labels"]["v_AVOID"] == nt(lang, "v_AVOID")
    script = N.LANG_SCRIPT[lang]
    assert N.syllables(26, 2, script)[0] in html            # the birth pada's letter in the page script
    assert "Trichy" in html and 'data-carry-to="/horoscope"' in html
    # same page after the details are given: form and birth star side by side, letters and numbers below
    assert html.index('action="/baby-names"') < html.index('id="nm-star"') < html.index('id="nm-results"')
    assert 'value="2024-03-12"' in html and 'value="06:42"' in html and 'id="nm-try" hidden' not in html
    # the parts the page fetches as the details are typed match the server-rendered page
    from app.web.ui import localize_links
    assert localize_links(views.naming_star(lang, frm, "Trichy", data), lang) in html
    assert localize_links(views.naming_cards(lang, frm, data), lang) in html


def test_find_letters_links_open_the_result():
    from app.web import views
    from app.web.forms import HoroscopeForm
    from app.web.settings import Settings
    frm = HoroscopeForm.parse({"name": ["Asha"], "sex": ["F"], "dob": ["2024-03-12"], "tob": ["06:42"],
                               "place": ["Trichy"], "lat": ["10.8"], "lon": ["78.69"], "lang": ["en"]})
    rp = ResolvedPerson(frm.birth.to_person())
    chart = rp.chart(frm.ayanamsa)
    html = views.horoscope_result(Settings(), frm, "Trichy", chart, {"RASI": "", "NAVAMSA": ""})
    link = html.split('data-carry-to="/baby-names"')[1].split(">")[0]
    assert 'data-carry-submit="1"' in link


def test_naming_form_errors():
    from app.web.forms import NamingForm
    frm = NamingForm.parse({"dob": [""], "tob": ["06:42"]})
    assert "dob" in frm.errors and "place" in frm.errors and "name" not in frm.errors and "sex" not in frm.errors


def test_js_matches_python():
    """naming.js runs the same arithmetic and first-sound rules as the Python engine."""
    import json
    import shutil
    import subprocess
    from pathlib import Path
    node = shutil.which("node")
    if not node:
        pytest.skip("node not installed")
    js = Path(__file__).resolve().parents[1] / "app" / "web" / "static" / "naming.js"
    names = ["Aarav", "Charan", "Lakshmi", "Vivek Ananth", "Bi", "Zoë", "Ramanathan", "Aishwarya", "Thilak",
             "Prakash", "Dhruv", "Moorthy", "Meenakshi", "தேவி", "देविका", "Chudar"]
    T = {"chaldean": R.CHALDEAN, "pythagorean": R.PYTHAGOREAN, "masters": list(R.MASTER_NUMBERS)}
    star = N.star_syllables(26)
    prog = f"""const NM = require({json.dumps(str(js))});
const T = {json.dumps(T)}, star = {json.dumps(star, ensure_ascii=False)}, names = {json.dumps(names, ensure_ascii=False)};
console.log(JSON.stringify(names.map(n => {{ const c = NM.chaldean(n, T), p = NM.pythagorean(n, T);
  return [c.total, c.number, p.total, p.number, p.digit, NM.pyramid(c.letters.map(v => v[1]), T).apex,
          NM.firstSound(n, star, 2)]; }})));"""
    # run from a UTF-8 file and read UTF-8 back: on Windows the console code page would garble Tamil/Devanagari
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "parity.js"
        f.write_text(prog, encoding="utf-8")
        run = subprocess.run([node, str(f)], capture_output=True, check=True)
    out = json.loads(run.stdout.decode("utf-8"))
    for name, got in zip(names, out):
        c, p = NU.chaldean(name), NU.pythagorean(name)
        want = [c["total"], c["number"], p["total"], p["number"], p["digit"],
                NU.pyramid([v for _, v in c["letters"]])["apex"], N.first_sound(name, 26, 2)]
        assert got == want, name
