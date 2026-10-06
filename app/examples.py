"""Request examples shown as a dropdown in the Swagger UI (/docs)."""

_BY_PLACE = {"name": "Arun", "sex": "M", "dob": "1987-08-12", "tob": "06:10 AM", "place": "Trichy, Tamil Nadu, India"}
_BY_COORDS = {"name": "Priya", "sex": "F", "dob": "1991-09-23", "tob": "06:30", "lat": 13.0827, "lon": 80.2707}
_WITH_OFFSET = {"sex": "M", "dob": "1950-03-10", "tob": "06:15 AM", "lat": 18.9750, "lon": 72.8258,
                "utcOffset": "+04:51"}

# Invented people with coordinates in arc-minutes, the way astrologers' atlases list them
_ATLAS_CHENNAI = {"name": "Meena", "sex": "F", "dob": "2012-04-18", "tob": "09:25",
                  "lat": 13.066667, "lon": 80.283333}   # Chennai 13°04'N 80°17'E
_ATLAS_COIMBATORE = {"name": "Karthik", "sex": "M", "dob": "1999-12-02", "tob": "23:40",
                     "lat": 11.016667, "lon": 77.0}     # Coimbatore 11°01'N 77°00'E

MATCH_EXAMPLES = {
    "place_and_coords": {
        "summary": "One by place, one by lat/lon (all methods)",
        "value": {
            "personA": _BY_PLACE,
            "personB": _BY_COORDS,
            "options": {"ayanamsa": "LAHIRI", "methods": ["ASHTAKOOTA", "PORUTHAM", "MANGLIK", "RAHU_KETU", "KP_7TH_CUSP"],
                        "positions": "TRUE"},
        },
    },
    "both_by_place": {
        "summary": "Both by place, selected methods only",
        "value": {
            "personA": _BY_PLACE,
            "personB": {"name": "Kavya", "sex": "F", "dob": "1988-11-02", "tob": "21:10", "place": "Madurai, Tamil Nadu"},
            "options": {"ayanamsa": "KP", "methods": ["ASHTAKOOTA", "PORUTHAM"]},
        },
    },
    "coords_with_offset": {
        "summary": "lat/lon with utcOffset override (e.g. old Bombay Time birth)",
        "value": {
            "personA": _WITH_OFFSET,
            "personB": {**_BY_COORDS, "dob": "1955-08-21"},
            "options": {"ayanamsa": "LAHIRI", "methods": ["ASHTAKOOTA", "PORUTHAM", "MANGLIK", "RAHU_KETU", "KP_7TH_CUSP"]},
        },
    },
}

CHART_EXAMPLES = {
    "by_place": {"summary": "By place", "value": {"person": _BY_PLACE, "ayanamsa": "LAHIRI"}},
    "by_coords": {"summary": "By lat/lon", "value": {"person": _BY_COORDS, "ayanamsa": "LAHIRI"}},
    "atlas_kp": {
        "summary": "Atlas coordinates (arc-minutes), KP ayanamsa, true positions",
        "value": {"person": _ATLAS_CHENNAI, "ayanamsa": "KP", "positions": "TRUE"},
    },
    "atlas_kp_2": {
        "summary": "Atlas coordinates, KP ayanamsa (second example)",
        "value": {"person": _ATLAS_COIMBATORE, "ayanamsa": "KP", "positions": "TRUE"},
    },
    "coords_with_offset": {
        "summary": "lat/lon with utcOffset override",
        "description": "utcOffset is only used with lat/lon; it is ignored when 'place' is given.",
        "value": {"person": _WITH_OFFSET, "ayanamsa": "KP", "positions": "APPARENT"},
    },
}

IMAGE_EXAMPLES = {
    "atlas_tamil": {
        "summary": "Atlas coordinates, KP, Tamil, all parts",
        "value": {"person": _ATLAS_CHENNAI, "ayanamsa": "KP", "lang": "ta",
                  "include": ["RASI", "NAVAMSA", "KP_TABLES"]},
    },
    "atlas_english": {
        "summary": "Atlas coordinates, KP, English, all parts",
        "value": {"person": _ATLAS_COIMBATORE, "ayanamsa": "KP", "lang": "en",
                  "include": ["RASI", "NAVAMSA", "KP_TABLES"]},
    },
    "tamil_all": {
        "summary": "Tamil labels, Rasi + Navamsa + KP tables",
        "value": {"person": _BY_PLACE, "ayanamsa": "KP", "lang": "ta",
                  "include": ["RASI", "NAVAMSA", "KP_TABLES"]},
    },
    "english_rasi_only": {
        "summary": "English, Rasi chart only",
        "value": {"person": _BY_COORDS, "lang": "en", "include": ["RASI"]},
    },
    "hindi": {
        "summary": "Hindi labels, charts only",
        "value": {"person": _BY_PLACE, "lang": "hi", "include": ["RASI", "NAVAMSA"]},
    },
}
