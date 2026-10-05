"""Rule tests on synthetic charts. Expected values are hand-computed from rules/v1.py."""
from app.core.ayanamsa import Ayanamsa
from app.matching import ashtakoota, kp, manglik, porutham
from app.rules import v1 as R

from .helpers import make_chart

ROHINI_VRISHABHA = 45.0   # Rohini, Vrishabha
MAGHA_SIMHA = 125.0       # Magha, Simha
ASHWINI_P1 = 1.0          # Ashwini pada 1, Mesha


def _koota(res, name):
    return next(k for k in res["details"]["kootas"] if k["name"] == name)


def _dosha(res, name):
    return next(d for d in res["details"]["doshas"] if d["name"] == name)


# ------------------------------------------------------------ tables
def test_tables_have_27_and_12_entries():
    assert len(R.GANA) == len(R.NADI) == len(R.YONI) == len(R.RAJJU) == 27
    assert len(R.VARNA) == len(R.VASHYA_BY_RASHI) == 12


def test_yoni_matrix_symmetric_with_seven_enemy_pairs():
    m = R.YONI_SCORE
    assert all(m[i][j] == m[j][i] for i in range(14) for j in range(14))
    assert sum(1 for i in range(14) for j in range(i + 1, 14) if m[i][j] == 0) == 7


def test_each_gana_and_nadi_has_nine_stars():
    for k in "DMR":
        assert R.GANA.count(k) == 9
    for k in "AMN":
        assert R.NADI.count(k) == 9


# -------------------------------------------------------- Ashtakoota
def test_same_star_same_pada_is_28_with_nadi_dosha():
    res = ashtakoota.match(make_chart(ASHWINI_P1), make_chart(ASHWINI_P1))
    assert res["score"]["total"] == 28
    assert _koota(res, "Nadi")["score"] == 0
    assert _dosha(res, "Nadi")["status"] == "PRESENT"
    assert res["result"] == "UTTAMAM"


def test_same_star_different_pada_cancels_nadi():
    res = ashtakoota.match(make_chart(1.0), make_chart(5.0))  # Ashwini p1 vs p2
    assert _dosha(res, "Nadi")["status"] == "CANCELLED"
    assert res["score"]["totalWithCancellations"] == res["score"]["total"] + 8


def test_rohini_boy_magha_girl():
    res = ashtakoota.match(make_chart(ROHINI_VRISHABHA), make_chart(MAGHA_SIMHA))
    scores = {k["name"]: k["score"] for k in res["details"]["kootas"]}
    assert scores == {"Varna": 0, "Vashya": 0.5, "Tara": 1.5, "Yoni": 1, "Graha Maitri": 0,
                      "Gana": 0, "Bhakoot": 7, "Nadi": 0}
    assert res["score"]["total"] == 10
    assert res["result"] == "ADHAMAM"
    assert _dosha(res, "Nadi")["status"] == "PRESENT"
    assert _dosha(res, "Gana")["status"] == "CANCELLED"
    assert res["score"]["totalWithCancellations"] == 16


def test_ashtakoota_bands():
    from app.matching.common import band
    assert band(17.5, R.ASHTAKOOTA_BANDS)[0] == "ADHAMAM"
    assert band(18, R.ASHTAKOOTA_BANDS)[0] == "MADHYAMAM"
    assert band(25, R.ASHTAKOOTA_BANDS)[0] == "UTTAMAM"
    assert band(33, R.ASHTAKOOTA_BANDS)[0] == "ATI_UTTAMAM"


# ---------------------------------------------------------- Porutham
def test_porutham_rohini_boy_magha_girl():
    res = porutham.match(make_chart(ROHINI_VRISHABHA), make_chart(MAGHA_SIMHA))
    st = {i["name"]: i["status"] for i in res["details"]["items"]}
    assert st == {
        "Dina": "NO_MATCH", "Gana": "NO_MATCH", "Mahendra": "MATCH", "Stree Deergha": "MATCH",
        "Yoni": "PARTIAL", "Rasi": "MATCH", "Rasyadhipathi": "NO_MATCH", "Vasya": "NO_MATCH",
        "Rajju": "MATCH", "Vedha": "MATCH", "Varna": "NO_MATCH", "Nadi": "NO_MATCH",
    }
    # Both Antya nadi → rejected regardless of the rest
    assert res["score"]["strict"]["result"] == "REJECTED" and "Nadi" in res["score"]["strict"]["label"]
    assert res["score"]["strict"]["of"] == 12 and res["score"]["strict"]["matched"] == 5


def _grade(b, g):
    r = porutham.match(make_chart(b), make_chart(g))
    return r["score"]["strict"]["result"], r["score"]["lenient"]["result"], r


def test_uttamam_when_all_key_poruthams_match():
    # Boy Ashwini (Mesha), girl Bharani (Mesha): Rajju Pada/Kati, Varna equal, Nadi Adi/Madhya,
    # same rasi different star, same lord (Mars), Stree Deergha count 27
    strict, lenient, r = _grade(1.6, 14.93)
    assert (strict, lenient) == ("UTTAMAM", "UTTAMAM") and r["score"]["strict"]["keyNotMatched"] == []


def test_madhyamam_when_rajju_matches_but_key_porutham_fails():
    # Boy Ashwini (Mesha), girl Mrigashira (Mithuna): Rasyadhipathi Mars/Mercury are enemies
    strict, lenient, r = _grade(1.6, 61.6)
    assert (strict, lenient) == ("MADHYAMAM", "MADHYAMAM")
    assert r["score"]["strict"]["keyNotMatched"] == ["Rasyadhipathi"]


def test_partial_key_porutham_lifts_lenient_only():
    # Boy Ashwini (Mesha), girl Krittika (Vrishabha): Rasi and Rasyadhipathi are PARTIAL
    strict, lenient, _ = _grade(1.6, 31.6)
    assert (strict, lenient) == ("MADHYAMAM", "UTTAMAM")


def test_adhamam_when_rajju_fails():
    # Boy Ashwini, girl Ashlesha: both Pada rajju; nadi differs so not rejected
    strict, lenient, _ = _grade(1.6, 108.27)
    assert (strict, lenient) == ("ADHAMAM", "ADHAMAM")


def test_same_nadi_rejects_both_views():
    res = porutham.match(make_chart(ASHWINI_P1), make_chart(ASHWINI_P1))
    assert res["score"]["strict"]["result"] == res["score"]["lenient"]["result"] == "REJECTED"


def test_same_star_different_pada_nadi_is_excused():
    # Ashwini pada 1 vs pada 2: same nadi, but the exception applies → not rejected
    res = porutham.match(make_chart(1.0), make_chart(5.0))
    nadi = next(i for i in res["details"]["items"] if i["name"] == "Nadi")
    assert nadi["status"] == "MATCH" and nadi["exception"] == "Same nakshatra but different pada"
    assert res["score"]["strict"]["result"] != "REJECTED"


def test_same_rashi_different_star_nadi_is_excused():
    # Rohini (Vrishabha, Antya) vs Krittika pada 2 (Vrishabha, Antya)
    res = porutham.match(make_chart(45.0), make_chart(31.6))
    nadi = next(i for i in res["details"]["items"] if i["name"] == "Nadi")
    assert nadi["status"] == "MATCH" and nadi["exception"] == "Same rashi but different nakshatra"


def test_vedha_pair_rejects():
    boy, girl = make_chart(3 * 13.3334 + 1), make_chart(14 * 13.3334 + 1)  # Rohini–Swati
    res = porutham.match(boy, girl)
    assert next(i for i in res["details"]["items"] if i["name"] == "Vedha")["status"] == "NO_MATCH"
    assert res["result"] == "REJECTED"


def test_varna_boy_lower_than_girl_fails():
    # Boy Mithuna (Shudra), girl Karka (Brahmin)
    res = porutham.match(make_chart(65.0), make_chart(95.0))
    assert next(i for i in res["details"]["items"] if i["name"] == "Varna")["status"] == "NO_MATCH"


# ------------------------------------------------------------ Manglik
def test_mars_fourth_from_lagna_is_high():
    c = make_chart(200.0, asc=5.0, Mars=95.0, Venus=300.0, Jupiter=250.0)
    a = manglik.assess(c)
    assert a["status"] == "HIGH" and "fromLagna" in a["afflictedFrom"]


def test_mars_in_own_sign_is_cancelled():
    a = manglik.assess(make_chart(200.0, asc=5.0, Mars=15.0, Venus=300.0, Jupiter=250.0))
    assert a["status"] == "CANCELLED" and a["doshaLevel"] == "HIGH"


def test_no_dosha():
    a = manglik.assess(make_chart(100.0, asc=100.0, Mars=160.0, Venus=100.0))  # Mars 3rd from all
    assert a["status"] == "NONE"


def test_manglik_pair_results():
    high = make_chart(200.0, asc=5.0, Mars=95.0, Venus=300.0, Jupiter=250.0)
    none = make_chart(100.0, asc=100.0, Mars=160.0, Venus=100.0)
    assert manglik.match(high, none)["result"] == "MISMATCH"
    assert manglik.match(high, high)["result"] == "MUTUAL"
    assert manglik.match(none, none)["result"] == "NO_DOSHA"


# ----------------------------------------------------------------- KP
def test_kp_promise_rules():
    assert kp._promise({2, 7, 11}) == "STRONG"
    assert kp._promise({2, 11, 4}) == "STRONG"
    assert kp._promise({7, 11, 6}) == "PROMISED"
    assert kp._promise({7, 6, 10}) == "MIXED"
    assert kp._promise({2, 11, 6}) == "DENIED"
    assert kp._promise({3, 4, 5}) == "DENIED"


def test_kp_significations_levels():
    # asc 0 with equal synthetic houses: Venus at 121 (house 5, Magha star → lord Ketu)
    c = make_chart(10.0, asc=0.0, model=Ayanamsa.KP, Venus=121.0, Rahu=200.0)
    sig = kp.significations_four_level(c, "Venus")
    assert sig["starLord"] == "Ketu"
    assert sig["levels"]["occupies"] == [5]
    assert sig["levels"]["owns"] == [2, 7]  # Vrishabha & Tula cusps


def test_kp_house_significators_rule():
    # Occupied house → planets in the occupant's star (else the occupant); empty → via the cusp's sign lord.
    c = make_chart(10.0, asc=0.0, model=Ayanamsa.KP, Venus=121.0, Rahu=200.0)
    hs = kp.house_significators(c)
    for h, sig in hs.items():
        assert sig, f"house {h} has no significator"
    # House 5 holds only Venus; Ketu (20°, Bharani) is in Venus's star → Ketu signifies 5, not Venus
    assert hs[5] == ["Ketu"]
    # House 3 is empty; its lord Mercury (110°, Ashlesha) sits in its own star → Mercury
    assert hs[3] == ["Mercury"]


def test_cancelled_bhakoot_restores_seven_points():
    # Astrologer's sample pair: boy Moon Mesha (Bharani), girl Moon Simha (Magha) — 9/5 Bhakoot,
    # cancelled because Mars and Sun are friends → astrologer gives 7
    res = ashtakoota.match(make_chart(24.61), make_chart(125.80))
    bk = _koota(res, "Bhakoot")
    assert bk["score"] == 7 and bk["rawScore"] == 0
    assert _dosha(res, "Bhakoot")["status"] == "CANCELLED"
    assert res["score"]["total"] == res["score"]["rawTotal"] + 7
    # Gana is also cancelled but (per astrologer) does not get its points back
    assert _koota(res, "Gana")["score"] == 0
    assert res["score"]["totalWithCancellations"] == res["score"]["total"] + 6
