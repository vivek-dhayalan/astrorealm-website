import xml.dom.minidom

from app import service
from app.schemas import ChartImageRequest

PERSON = {"sex": "F", "dob": "2015-01-28", "tob": "10:30", "lat": 13.08784, "lon": 80.27847}


def _svg(**kw):
    return service.run_chart_image(ChartImageRequest.model_validate({"person": PERSON, **kw}))


def test_svg_is_valid_and_has_all_parts():
    s = _svg(name="Test", ayanamsa="KP")
    xml.dom.minidom.parseString(s)
    assert "Rasi" in s and "Navamsa" in s and "KP planets" in s and "KP cusps" in s
    assert "Me(R)" in s and "Ju(R)" in s


def test_tamil_labels():
    s = _svg(lang="ta")
    assert "நவாம்சம்" in s and "சந்" in s and "(வ)" in s


def test_hindi_labels():
    s = _svg(lang="hi", include=["RASI"])
    assert "राशि चक्र" in s and "नवांश" not in s


def test_include_filter():
    s = _svg(include=["NAVAMSA"])
    assert "Navamsa" in s and "KP cusps" not in s


def test_person_name_in_heading_and_legacy_name_still_works():
    s = service.run_chart_image(ChartImageRequest.model_validate({"person": {**PERSON, "name": "Meena"}}))
    assert "Meena" in s
    assert "Legacy" in _svg(name="Legacy")
