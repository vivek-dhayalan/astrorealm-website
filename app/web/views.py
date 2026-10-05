"""HTML for the website, built with plain functions (no template engine).

Every user-supplied value goes through esc(); the only raw HTML inserted is the sanitized
description and SVGs we render ourselves.
"""
from __future__ import annotations

from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from ..core.reference import NAKSHATRAS, RASHIS
from ..render import i18n
from .learn import ARTICLES, Article
from .forms import CHART_PARTS, BirthInput, HoroscopeForm, MatchForm
from .settings import Settings
from .strings import LANG_NAMES, LANGS, t

FONTS_URL = ("https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;600;700"
             "&family=Noto+Sans+Tamil:wght@400;600;700&family=Noto+Sans+Telugu:wght@400;600;700"
             "&family=Noto+Sans+Malayalam:wght@400;600;700&family=Noto+Sans+Kannada:wght@400;600;700"
             "&family=Noto+Sans+Devanagari:wght@400;600;700&display=swap")
MAPLIBRE_VERSION = "4.7.1"
MAP_CSS = f'<link rel="stylesheet" href="https://unpkg.com/maplibre-gl@{MAPLIBRE_VERSION}/dist/maplibre-gl.css">'
MAP_JS = f'<script src="https://unpkg.com/maplibre-gl@{MAPLIBRE_VERSION}/dist/maplibre-gl.js"></script>'
# Consent Mode v2: everything denied by default for EEA, UK and Switzerland until Google's consent message
# (AdSense → Privacy & messaging) records a choice; granted elsewhere.
CONSENT_REGIONS = ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT", "LV",
                   "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE", "IS", "LI", "NO", "GB", "CH"]


def analytics_tags(measurement_id: str) -> str:
    regions = ",".join(f"'{r}'" for r in CONSENT_REGIONS)
    return (f'<script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>'
            "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
            "gtag('consent','default',{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',"
            f"analytics_storage:'denied',region:[{regions}]}});"
            f"gtag('js',new Date());gtag('config','{measurement_id}');</script>")


TURNSTILE_JS = '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>'
STATIC_VERSION = "1"


def esc(v) -> str:
    return escape("" if v is None else str(v), quote=True)


# ------------------------------------------------------------------ layout pieces
def ad_slot(s: Settings, slot_id: str, kind: str) -> str:
    if s.ads_enabled and slot_id:
        return (f'<aside class="ad ad-{kind} no-print" aria-label="Advertisement">'
                f'<ins class="adsbygoogle" style="display:block" data-ad-client="{esc(s.adsense_client)}" '
                f'data-ad-slot="{esc(slot_id)}" data-ad-format="auto" data-full-width-responsive="true"></ins>'
                f'<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script></aside>')
    return ""  # no AdSense configured for this slot: no space is reserved


def layout(s: Settings, title: str, body: str, *, active: str = "", map_page: bool = False,
           turnstile: bool = False, side_ad: bool = True, ads: bool = True) -> str:
    """ads=False for result pages: they hold names and birth details, so no ad or analytics script runs there."""
    ads_on = ads and s.ads_enabled
    ga_on = ads and s.analytics_enabled
    head_extra = []
    if map_page:
        head_extra.append(MAP_CSS)
    if turnstile and s.turnstile_enabled:
        head_extra.append(TURNSTILE_JS)
    if ga_on:
        head_extra.append(analytics_tags(s.ga_measurement_id))  # id validated as G-XXXX in settings
    if ads_on:
        head_extra.append(f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
                          f'?client={esc(s.adsense_client)}" crossorigin="anonymous"></script>')
    cur = ' aria-current="page"'
    nav = "".join(
        f'<a href="{href}"{cur if key == active else ""}>{label}</a>'
        for key, href, label in (("horoscope", "/horoscope", "Horoscope"), ("match", "/match", "Matching"),
                                 ("learn", "/learn", "Learn"), ("credits", "/credits", "Credits")))
    source = f' · <a href="{esc(s.source_url)}" rel="noopener">Source code</a>' if s.source_url else ""
    consent = ""
    if ads_on or ga_on:
        what = " and ".join(x for x, on in (("ads from Google AdSense", ads_on),
                                             ("Google Analytics to count visits", ga_on)) if on)
        consent = (f'<div class="consent no-print" id="consent" hidden><p>We use {what}, which use cookies. '
                   'Your birth details are never shared with Google. '
                   '<a href="/privacy">Privacy</a></p><button type="button" data-action="consent-ok">OK</button></div>')
    side = ad_slot(s, s.adsense_slot_side, "side") if (side_ad and ads) else ""
    top = ad_slot(s, s.adsense_slot_top, "top") if ads else ""
    bottom = ad_slot(s, s.adsense_slot_bottom, "bottom") if ads else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · {esc(s.site_name)}</title>
<meta name="description" content="Free horoscope (jathagam) and marriage matching — Ashtakoota and Porutham — in English, Tamil, Telugu, Malayalam, Kannada and Hindi.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS_URL}">
<link rel="stylesheet" href="/static/site.css?v={STATIC_VERSION}">
{''.join(head_extra)}
</head>
<body data-map-style="{esc(s.map_style_url)}">
<a class="skip" href="#main">Skip to content</a>
<header class="site-head no-print"><a class="brand" href="/">{esc(s.site_name)}</a><nav>{nav}</nav></header>
{top}
<div class="page{' with-side' if side else ''}">
<main id="main">{body}</main>
{side}
</div>
{bottom}
<footer class="site-foot no-print">
<p>Free to use. For guidance only — consult an astrologer before taking decisions.</p>
<p><a href="/learn">Learn</a> · <a href="/privacy">Privacy</a> · <a href="/terms">Terms</a> · <a href="/credits">Credits</a>{source}</p>
<p class="small">Place data © <a href="https://www.geonames.org/" rel="noopener">GeoNames</a> (CC BY 4.0).
Calculations use the Swiss Ephemeris © Astrodienst AG.</p>
</footer>
{consent}
{MAP_JS if map_page else ''}
<script src="/static/site.js?v={STATIC_VERSION}" defer></script>
</body>
</html>"""


# ------------------------------------------------------------------ form widgets
def _err(errors: dict, key: str) -> str:
    return f'<p class="err" id="{esc(key)}-err">{esc(errors[key])}</p>' if key in errors else ""


def _aria(errors: dict, key: str) -> str:
    return f' aria-invalid="true" aria-describedby="{esc(key)}-err"' if key in errors else ""


def text_field(key: str, label: str, value: str, errors: dict, *, type_: str = "text", required: bool = False,
               maxlength: int = 80, hint: str = "", extra: str = "") -> str:
    req = " required" if required else ""
    h = f'<p class="hint">{esc(hint)}</p>' if hint else ""
    return (f'<div class="field"><label for="{key}">{esc(label)}{" *" if required else ""}</label>'
            f'<input id="{key}" name="{key}" type="{type_}" value="{esc(value)}" maxlength="{maxlength}"'
            f'{req}{_aria(errors, key)}{extra}>{h}{_err(errors, key)}</div>')


TIPS = {
    "ayanamsa": ("What is Ayanamsa?",
                 "Indian astrology measures planets against the fixed stars (sidereal zodiac). Ayanamsa is the gap "
                 "between that and the Western (tropical) zodiac — about 24° today, growing by roughly 50″ a year. "
                 "Lahiri (Chitrapaksha) is the Indian government standard; Krishnamurti (KP) is about 6′ smaller and "
                 "is used in KP astrology. Choose the one your astrologer uses.", "/learn/ayanamsa"),
    "RASI": ("What is the Rasi chart?",
             "The main birth chart (D-1): where the Lagna (ascendant) and the nine planets stood in the twelve "
             "signs at the moment of birth. Shown in the South Indian layout, where the signs stay fixed — Meena "
             "at top left, then clockwise.", "/learn/rasi-navamsa"),
    "NAVAMSA": ("What is the Navamsa chart?",
                "The ninth-division chart (D-9). Each sign is split into nine parts of 3°20′, and each planet is "
                "placed by the part it falls in. Traditionally read for marriage, the spouse and the real strength "
                "of planets.", "/learn/rasi-navamsa"),
    "KP_TABLES": ("What are the KP tables?",
                  "Krishnamurti Paddhati tables: for every planet and house cusp, the sign lord, star (nakshatra) "
                  "lord, sub lord and finer sub-sub levels, plus the houses each one signifies. Always calculated "
                  "with the KP ayanamsa. Prints on a second A5 page.", "/learn/kp-astrology"),
}


def tip(key: str) -> str:
    """Info button with a small popover (hover, focus or tap). Text is ours, never user input."""
    title, text, href = TIPS[key]
    tid = f"tip-{key.lower()}"
    return (f'<span class="tip"><button type="button" class="tip-btn" aria-expanded="false" aria-controls="{tid}" '
            f'aria-label="{esc(title)}" data-action="tip">i</button>'
            f'<span class="tip-box" id="{tid}" role="note"><b>{esc(title)}</b> {esc(text)} '
            f'<a href="{href}" target="_blank" rel="noopener">Learn more</a></span></span>')


def select_field(key: str, label: str, value: str, options: list[tuple[str, str]], errors: dict,
                 required: bool = False, blank: str | None = None, info: str = "") -> str:
    opts = f'<option value="">{esc(blank)}</option>' if blank is not None else ""
    opts += "".join(f'<option value="{esc(v)}"{" selected" if v == value else ""}>{esc(lbl)}</option>'
                    for v, lbl in options)
    lab = f'<label for="{key}">{esc(label)}{" *" if required else ""}</label>'
    if info:
        lab = f'<div class="label-row">{lab}{tip(info)}</div>'
    return (f'<div class="field">{lab}'
            f'<select id="{key}" name="{key}"{" required" if required else ""}{_aria(errors, key)}>{opts}</select>'
            f'{_err(errors, key)}</div>')


def place_field(prefix: str, b: BirthInput, errors: dict) -> str:
    key = prefix + "place"
    lat = "" if b.lat is None else f"{b.lat:.5f}"
    lon = "" if b.lon is None else f"{b.lon:.5f}"
    coords = f"{lat}, {lon}" if lat else ""
    return f"""<div class="field place-field" data-prefix="{prefix}">
<label for="{key}">Place of birth *</label>
<div class="place-box">
<input id="{key}" name="{key}" type="text" value="{esc(b.place)}" maxlength="120" autocomplete="off"
 placeholder="Start typing a town or city" role="combobox" aria-autocomplete="list" aria-expanded="false"
 aria-controls="{key}-list"{_aria(errors, key)}>
<ul class="suggest" id="{key}-list" role="listbox" hidden></ul>
</div>
<input type="hidden" name="{prefix}lat" value="{lat}"><input type="hidden" name="{prefix}lon" value="{lon}">
<p class="hint"><button type="button" class="linkish" data-action="map">Pick on map</button>
<span class="coords">{esc(coords)}</span></p>
<div class="map" hidden></div>
{_err(errors, key)}
</div>"""


def birth_fields(prefix: str, b: BirthInput, errors: dict, *, with_sex: bool) -> str:
    sex = select_field(prefix + "sex", "Sex", b.sex, [("F", "Female"), ("M", "Male")], errors, True,
                       blank="Choose") if with_sex else ""
    return (text_field(prefix + "name", "Name", b.name, errors, required=True, maxlength=80)
            + sex
            + '<div class="row2">'
            + text_field(prefix + "dob", "Date of birth", b.dob, errors, type_="date", required=True, maxlength=10)
            + text_field(prefix + "tob", "Time of birth", b.tob, errors, type_="time", required=True, maxlength=8,
                         hint="As on the birth record; 12- or 24-hour per your device.")
            + "</div>"
            + place_field(prefix, b, errors))


def common_options(lang: str, ayanamsa: str, errors: dict) -> str:
    return ('<div class="row2">'
            + select_field("lang", "Output language", lang, [(k, LANG_NAMES[k]) for k in LANGS], errors)
            + select_field("ayanamsa", "Ayanamsa", ayanamsa,
                           [("LAHIRI", "Lahiri (Chitrapaksha)"), ("KP", "Krishnamurti (KP)")], errors,
                           info="ayanamsa")
            + "</div>")


def turnstile_widget(s: Settings) -> str:
    if s.turnstile_enabled:
        return f'<div class="cf-turnstile" data-sitekey="{esc(s.turnstile_site_key)}" data-size="flexible"></div>'
    return '<p class="hint no-print">Bot check is off (local development).</p>'


def banner(message: str | None, candidates: list[dict] | None = None) -> str:
    if not message:
        return ""
    extra = ""
    if candidates:
        items = "".join(f"<li>{esc(c.get('name'))}, {esc(c.get('admin1') or '')} {esc(c.get('countryName') or '')}</li>"
                        for c in candidates)
        extra = f"<p>Pick one from the suggestions as you type, or use the map. Matches:</p><ul>{items}</ul>"
    return f'<div class="banner" role="alert"><p>{esc(message)}</p>{extra}</div>'


# ------------------------------------------------------------------ pages
def home(s: Settings) -> str:
    body = """<section class="hero"><h1>Free horoscope and marriage matching</h1>
<p>South Indian charts, Ashtakoota and 12-porutham matching, in English, தமிழ், తెలుగు, മലയാളം, ಕನ್ನಡ and हिन्दी.
Nothing you enter is saved.</p></section>
<div class="cards">
<a class="card" href="/horoscope"><h2>Horoscope</h2><p>Rasi and Navamsa charts with your family and personal details,
ready to print on A5.</p></a>
<a class="card" href="/match"><h2>Marriage matching</h2><p>Ashtakoota (36 gunas) and Porutham for a bride and groom,
with both Rasi charts.</p></a>
<a class="card" href="/learn"><h2>Learn</h2><p>Short guides to ayanamsa, Rasi and Navamsa charts, Ashtakoota, Porutham
and KP astrology.</p></a>
</div>"""
    return layout(s, "Horoscope and matching", body, active="")


def horoscope_form(s: Settings, frm: HoroscopeForm, message: str | None = None,
                   candidates: list[dict] | None = None) -> str:
    e = frm.errors
    b = frm.birth
    parts = "".join(
        f'<span class="check-wrap"><label class="check"><input type="checkbox" name="parts" value="{p}"'
        f'{" checked" if p in frm.parts else ""}> {lbl}</label>{tip(p)}</span>'
        for p, lbl in zip(CHART_PARTS, ("Rasi chart", "Navamsa chart", "KP planet & cusp tables")))
    num = lambda k, lbl: text_field(k, lbl, "" if getattr(frm, k) is None else str(getattr(frm, k)), e,  # noqa: E731
                                    type_="number", maxlength=2, extra=' min="0" max="20" inputmode="numeric"')
    living = [("living", "Living"), ("deceased", "Deceased")]
    body = f"""<h1>Horoscope</h1>
<p class="lead">Fill in the birth details. Only the starred fields are required.</p>
{banner(message, candidates)}
<form method="post" action="/horoscope" class="form" novalidate>
<fieldset><legend>Birth details</legend>
{birth_fields("", b, e, with_sex=True)}
</fieldset>
<fieldset><legend>Chart options</legend>
{common_options(frm.lang, frm.ayanamsa.value, e)}
<div class="field"><span class="label">Include</span><div class="checks">{parts}</div>{_err(e, "parts")}</div>
</fieldset>
<fieldset><legend>Family</legend>
<div class="row2">
{text_field("gothram", "Gothram (optional)", frm.gothram, e, maxlength=40)}
{text_field("mathulam", "Mathulam — mother's family gothram (optional)", frm.mathulam, e, maxlength=40)}
</div>
<div class="row2">
{select_field("father", "Father", frm.father, living, e, blank="—")}
{select_field("mother", "Mother", frm.mother, living, e, blank="—")}
</div>
<div class="row4">
{num("brothers", "Brothers")}{num("brothers_married", "…of whom married")}
{num("sisters", "Sisters")}{num("sisters_married", "…of whom married")}
</div>
{_err(e, "brothers")}{_err(e, "sisters")}
</fieldset>
<fieldset><legend>Personal details</legend>
<div class="row2">
{text_field("degree", "Education — degree", frm.degree, e, maxlength=80)}
{text_field("branch", "Education — branch / specialisation", frm.branch, e, maxlength=80)}
</div>
<div class="row2">
{text_field("occupation", "Work / occupation", frm.occupation, e, maxlength=120)}
{text_field("complexion", "Complexion (optional)", frm.complexion, e, maxlength=40)}
</div>
<div class="field"><label id="desc-label">About (any language)</label>
<div class="rte">
<div class="rte-bar" role="toolbar" aria-label="Formatting">
<button type="button" data-cmd="bold" title="Bold"><b>B</b></button>
<button type="button" data-cmd="italic" title="Italic"><i>I</i></button>
<button type="button" data-cmd="underline" title="Underline"><u>U</u></button>
<button type="button" data-cmd="insertUnorderedList" title="Bulleted list">• List</button>
<button type="button" data-cmd="insertOrderedList" title="Numbered list">1. List</button>
</div>
<div class="rte-area" contenteditable="true" role="textbox" aria-multiline="true" aria-labelledby="desc-label">{frm.description}</div>
<textarea name="description" hidden>{esc(frm.description)}</textarea>
</div>
<p class="hint">Up to about 4,000 characters. Type in any language.</p>
</div>
</fieldset>
{turnstile_widget(s)}
<p><button type="submit" class="primary">Generate horoscope</button></p>
</form>"""
    return layout(s, "Horoscope", body, active="horoscope", map_page=True, turnstile=True)


def match_form(s: Settings, frm: MatchForm, message: str | None = None,
               candidates: list[dict] | None = None) -> str:
    e = frm.errors
    body = f"""<h1>Marriage matching</h1>
<p class="lead">Enter the bride's details on the left and the groom's on the right.</p>
{banner(message, candidates)}
<form method="post" action="/match" class="form" novalidate>
<div class="pair-form">
<fieldset class="bride"><legend>Bride</legend>{birth_fields("b_", frm.bride, e, with_sex=False)}</fieldset>
<fieldset class="groom"><legend>Groom</legend>{birth_fields("g_", frm.groom, e, with_sex=False)}</fieldset>
</div>
<fieldset><legend>Options</legend>{common_options(frm.lang, frm.ayanamsa.value, e)}</fieldset>
{turnstile_widget(s)}
<p><button type="submit" class="primary">Check matching</button></p>
</form>"""
    return layout(s, "Marriage matching", body, active="match", map_page=True, turnstile=True)


# ------------------------------------------------------------------ printable output
def _fmt_date(d: str) -> str:
    y, m, dd = d.split("-")
    return f"{dd}-{m}-{y}"


def _fmt_time(tob: str) -> str:
    hh, mm = (int(x) for x in tob.split(":")[:2])
    ampm = "AM" if hh < 12 else "PM"
    return f"{hh:02d}:{mm:02d} ({(hh % 12) or 12:02d}:{mm:02d} {ampm})"


def method_line(lang: str, chart, engine: str) -> str:
    eng = "Swiss Ephemeris" if engine == "swisseph" else "built-in ephemeris"
    return (f'{esc(t(lang, "method"))}: {esc(t(lang, "ayanamsa"))} {esc(t(lang, chart.ayanamsa.value))} '
            f'({chart.ayanamsa_value:.4f}°) · {esc(t(lang, chart.position_mode.value))} · '
            f'{esc(t(lang, "houses_placidus"))} · {eng}')


def sheet_foot(s: Settings, lang: str, chart) -> str:
    today = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d-%m-%Y")
    site = esc(s.base_url or s.site_name)
    return (f'<footer class="sheet-foot"><p>{method_line(lang, chart, chart.engine)}</p>'
            f'<p>{esc(t(lang, "generated"))}: {today} · {site} · {esc(t(lang, "disclaimer"))}</p></footer>')


def _kv(rows: list[tuple[str, str]]) -> str:
    rows = [(k, v) for k, v in rows if v]
    if not rows:
        return ""
    return '<table class="kv">' + "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows) + "</table>"


def astro_rows(lang: str, chart) -> list[tuple[str, str]]:
    L = i18n.get(lang)
    m = chart.moon
    return [
        (esc(t(lang, "nakshatra")), f'{esc(L["nakshatra"][NAKSHATRAS[m.nakshatra]])}, {esc(t(lang, "pada"))} {m.pada}'),
        (esc(t(lang, "rasi")), esc(L["rashi"][RASHIS[m.rashi]])),
        (esc(t(lang, "lagna")), esc(L["rashi"][RASHIS[chart.lagna_rashi]])),
    ]


def toolbar(back: str) -> str:
    return (f'<div class="toolbar no-print"><button type="button" class="primary" data-action="print">Print</button>'
            f'<button type="button" data-action="back">Edit details</button><a href="{back}">Start again</a>'
            f'<span class="hint">Print on A5 paper with default margins and “Background graphics” on.</span></div>')


def horoscope_result(s: Settings, frm: HoroscopeForm, place_label: str, chart, svgs: dict[str, str]) -> str:
    lang = frm.lang
    b = frm.birth

    def sib(n, m):
        if n is None:
            return ""
        return str(n) + (f" ({esc(t(lang, 'married_n', n=m))})" if m else "")

    def parent(v):
        return esc(t(lang, v)) if v else ""

    edu = " — ".join(x for x in (frm.degree, frm.branch) if x)
    birth = _kv([
        (esc(t(lang, "sex")), esc(t(lang, b.sex))),
        (esc(t(lang, "dob")), esc(_fmt_date(b.dob))),
        (esc(t(lang, "tob")), esc(_fmt_time(b.tob))),
        (esc(t(lang, "pob")), esc(place_label)),
    ] + astro_rows(lang, chart))
    family = _kv([
        (esc(t(lang, "gothram")), esc(frm.gothram)),
        (esc(t(lang, "mathulam")), esc(frm.mathulam)),
        (esc(t(lang, "father")), parent(frm.father)),
        (esc(t(lang, "mother")), parent(frm.mother)),
        (esc(t(lang, "brothers")), sib(frm.brothers, frm.brothers_married)),
        (esc(t(lang, "sisters")), sib(frm.sisters, frm.sisters_married)),
    ])
    personal = _kv([
        (esc(t(lang, "education")), esc(edu)),
        (esc(t(lang, "occupation")), esc(frm.occupation)),
        (esc(t(lang, "complexion")), esc(frm.complexion)),
    ])
    sec = lambda key, html: f'<section class="block"><h3>{esc(t(lang, key))}</h3>{html}</section>' if html else ""  # noqa: E731
    about = sec("about", f'<div class="about">{frm.description}</div>' if frm.description else "")
    foot = sheet_foot(s, lang, chart)
    grids = "".join(f'<figure class="chart">{svgs[k]}</figure>' for k in ("RASI", "NAVAMSA") if k in svgs)
    grids_html = f'<div class="grids n{grids.count("<figure")}">{grids}</div>' if grids else ""
    right = sec("family", family) + sec("personal", personal)
    sheets = [f"""<section class="sheet single">
<header class="sheet-head"><h2>{esc(b.name)}</h2><p>{esc(t(lang, "horoscope"))}</p></header>
<div class="cols"><div>{sec("birth_details", birth)}</div><div>{right}</div></div>
{about}{grids_html}
{foot}</section>"""]
    if "KP_TABLES" in svgs:
        sheets.append(f'<section class="sheet kp-sheet"><header class="sheet-head small"><h2>{esc(b.name)}</h2>'
                      f'<p>KP</p></header><figure class="kp">{svgs["KP_TABLES"]}</figure>{foot}</section>')
    body = toolbar("/horoscope") + f'<div class="sheets" lang="{lang}">{"".join(sheets)}</div>'
    # generic title: names must not reach browser history, tab sync or any third-party script
    return layout(s, "Your horoscope", body, active="horoscope", side_ad=False, ads=False)


def _pair_grid(lang: str, frm: MatchForm, labels: dict[str, str], charts: dict, svgs: dict[str, str]) -> str:
    """Bride (left) and groom (right) in one grid, so every row — and the two charts — line up."""
    people = (("bride", frm.bride), ("groom", frm.groom))
    rows = {}
    for role, b in people:
        rows[role] = [
            (esc(t(lang, "dob")), esc(_fmt_date(b.dob))),
            (esc(t(lang, "tob")), esc(_fmt_time(b.tob))),
            (esc(t(lang, "pob")), esc(labels[role])),
        ] + astro_rows(lang, charts[role])
    cells = [f'<div class="who person {role}"><p class="role">{esc(t(lang, role))}</p><h3>{esc(b.name)}</h3></div>'
             for role, b in people]
    for (bk, bv), (gk, gv) in zip(rows["bride"], rows["groom"]):
        cells.append(f'<div class="k">{bk}</div><div class="v">{bv}</div>'
                     f'<div class="k g">{gk}</div><div class="v">{gv}</div>')
    cells += [f'<figure class="chart {role}">{svgs[role]}</figure>' for role, _ in people]
    return f'<div class="pair">{"".join(cells)}</div>'


def match_result(s: Settings, frm: MatchForm, labels: dict[str, str], charts: dict, svgs: dict[str, str],
                 ashta: dict, poru: dict) -> str:
    lang = frm.lang
    en = lang == "en"
    # bride first (left), groom second (right) — always
    pair = _pair_grid(lang, frm, labels, charts, svgs)

    k_rows = []
    for k in ashta["details"]["kootas"]:
        note = ""
        if "rawScore" in k:
            note = f' <span class="note">({k["rawScore"]:g} → {k["score"]:g}, {esc(t(lang, "restored"))})</span>'
        vals = f'<td>{esc(k.get("girl"))}</td><td>{esc(k.get("boy"))}</td>' if en else ""
        k_rows.append(f'<tr><th>{esc(t(lang, "k_" + k["name"]))}</th>{vals}'
                      f'<td class="num">{k["score"]:g}{note}</td><td class="num">{k["max"]:g}</td></tr>')
    vh = f'<th>{esc(t(lang, "bride"))}</th><th>{esc(t(lang, "groom"))}</th>' if en else ""
    sc = ashta["score"]
    doshas = ", ".join(f'{esc(t(lang, "k_" + d["name"]))}: {esc(t(lang, d["status"]))}' for d in ashta["details"]["doshas"])
    ashta_html = f"""<section class="block"><h3>{esc(t(lang, "ashtakoota"))}</h3>
<table class="grid"><thead><tr><th>{esc(t(lang, "koota"))}</th>{vh}<th class="num">{esc(t(lang, "score"))}</th>
<th class="num">{esc(t(lang, "max"))}</th></tr></thead><tbody>{"".join(k_rows)}</tbody>
<tfoot><tr><th>{esc(t(lang, "total"))}</th>{'<td></td><td></td>' if en else ''}<td class="num"><b>{sc["total"]:g}</b></td>
<td class="num">{sc["max"]}</td></tr></tfoot></table>
<p class="verdict v-{esc(ashta["result"])}">{esc(t(lang, "result"))}: <b>{esc(t(lang, ashta["result"]))}</b></p>
<p class="small">{esc(t(lang, "dosha"))} — {doshas}</p></section>"""

    p_rows = "".join(
        f'<tr><th>{esc(t(lang, "p_" + i["name"]))}</th><td class="st st-{esc(i["status"])}">{esc(t(lang, i["status"]))}</td>'
        + (f'<td class="small">{esc(i["reason"])}</td>' if en else "") + "</tr>"
        for i in poru["details"]["items"])

    def view(key):
        v = poru["score"][key]
        missing = ", ".join(esc(t(lang, "p_" + n)) for n in v["keyNotMatched"])
        miss = f' · {esc(t(lang, "key_missing"))}: {missing}' if missing else ""
        return (f'<p class="verdict v-{esc(v["result"])}">{esc(t(lang, key))}: <b>{esc(t(lang, v["result"]))}</b> · '
                f'{esc(t(lang, "matched_of", m=v["matched"], n=v["of"]))}{miss}</p>')

    poru_html = f"""<section class="block"><h3>{esc(t(lang, "porutham"))}</h3>
<table class="grid"><tbody>{p_rows}</tbody></table>{view("strict")}{view("lenient")}</section>"""

    foot = sheet_foot(s, lang, charts["bride"])
    title = f'{frm.bride.name} & {frm.groom.name}'
    sheets = (f"""<section class="sheet">
<header class="sheet-head"><h2>{esc(t(lang, "matching"))}</h2><p>{esc(title)}</p></header>
{pair}{foot}</section>"""
              f"""<section class="sheet"><header class="sheet-head small"><h2>{esc(title)}</h2></header>
{ashta_html}{poru_html}{foot}</section>""")
    body = toolbar("/match") + f'<div class="sheets" lang="{lang}">{sheets}</div>'
    return layout(s, "Matching result", body, active="match", side_ad=False, ads=False)


# ------------------------------------------------------------------ static content pages
CREDITS = [
    ("Swiss Ephemeris", "https://www.astro.com/swisseph/", "© Astrodienst AG — AGPL-3.0",
     "Planetary positions and houses"),
    ("pyswisseph", "https://github.com/astrorigin/pyswisseph", "AGPL-3.0", "Python bindings for the Swiss Ephemeris"),
    ("GeoNames", "https://www.geonames.org/", "CC BY 4.0", "Place names, coordinates and time zones"),
    ("OpenStreetMap", "https://www.openstreetmap.org/copyright", "ODbL", "Map data"),
    ("MapLibre GL JS", "https://maplibre.org/", "BSD-3-Clause", "Interactive map"),
    ("OpenFreeMap", "https://openfreemap.org/", "Free service; map data © OpenStreetMap contributors (ODbL)",
     "Map tiles for “Pick on map”"),
    ("FastAPI", "https://fastapi.tiangolo.com/", "MIT", "Web framework"),
    ("Starlette", "https://www.starlette.io/", "BSD-3-Clause", "Web toolkit under FastAPI"),
    ("Pydantic", "https://docs.pydantic.dev/", "MIT", "Data validation"),
    ("Uvicorn", "https://www.uvicorn.org/", "BSD-3-Clause", "Web server"),
    ("RapidFuzz", "https://github.com/rapidfuzz/RapidFuzz", "MIT", "Fuzzy place-name search"),
    ("tzdata / IANA time zone database", "https://www.iana.org/time-zones", "Public domain / Apache-2.0",
     "Historical time zones"),
    ("Noto fonts", "https://fonts.google.com/noto", "SIL Open Font License 1.1",
     "Tamil, Telugu, Malayalam, Kannada and Devanagari text"),
    ("Cloudflare Turnstile", "https://www.cloudflare.com/products/turnstile/", "Service", "Bot protection"),
    ("Jean Meeus, Astronomical Algorithms; JPL approximate planetary elements", "https://ssd.jpl.nasa.gov/",
     "Published methods", "Fallback calculation engine"),
]


def credits(s: Settings) -> str:
    rows = "".join(f'<tr><th><a href="{esc(u)}" rel="noopener">{esc(n)}</a></th><td>{esc(lic)}</td><td>{esc(use)}</td></tr>'
                   for n, u, lic, use in CREDITS)
    src = (f'<p>This site is free software under the GNU Affero General Public License v3. '
           f'<a href="{esc(s.source_url)}" rel="noopener">Get the source code</a>.</p>' if s.source_url else
           '<p>This site is free software under the GNU Affero General Public License v3.</p>')
    body = f"""<h1>Credits</h1>{src}
<p>Built with these projects and data sources — thank you to their authors.</p>
<table class="grid credits"><thead><tr><th>Project</th><th>Licence</th><th>Used for</th></tr></thead><tbody>{rows}</tbody></table>
<p class="small">Matching rules follow traditional Ashtakoota and South Indian Porutham practice; the exact tables are
in the source code (<code>app/rules/v1.py</code>).</p>"""
    return layout(s, "Credits", body, active="credits")


def privacy(s: Settings) -> str:
    contact = f' Write to <a href="mailto:{esc(s.contact_email)}">{esc(s.contact_email)}</a>.' if s.contact_email else ""
    # list only the services that are actually switched on
    ads_li = ('<li><b>Google AdSense</b> shows ads and uses cookies for that. You can manage ad personalisation at '
              '<a href="https://adssettings.google.com/" rel="noopener">adssettings.google.com</a>.</li>'
              if s.ads_enabled else "")
    ga_li = ('<li><b>Google Analytics</b> counts visits to our pages (which pages, roughly where from, which device) '
             'using cookies. It does not run on the pages that show your horoscope or matching result. You can opt '
             'out with <a href="https://tools.google.com/dlpage/gaoptout" rel="noopener">Google\'s opt-out add-on</a>.</li>'
             if s.analytics_enabled else "")
    body = f"""<h1>Privacy</h1>
<p><b>We don't keep what you enter.</b> Names, birth details, family details and descriptions are used only to build
the page you asked for, then discarded. They are not stored, logged or sent to advertisers.</p>
<h2>What is processed</h2>
<ul>
<li>Your form entries — only while your page is generated.</li>
<li>Your IP address — briefly, in memory, to limit abuse (too many requests).</li>
<li>Place search — the letters you type are sent to our own server to suggest places.</li>
</ul>
<h2>Third parties</h2>
<ul>
<li><b>Google Cloud</b> (Cloud Run and Firebase Hosting, Mumbai region) hosts the site.</li>
<li><b>Cloudflare</b> runs the Turnstile bot check on the forms.</li>
{ads_li}{ga_li}<li><b>Google Fonts</b> and <b>unpkg</b> serve fonts and the map library; <b>OpenFreeMap</b> serves the map images
when you use “Pick on map”.</li>
</ul>
<p>None of them receive your form entries. Pages that show your horoscope or matching result carry no ads or
analytics.</p>
<h2>Your choices</h2>
<p>Because nothing is stored, there is nothing to delete. Printing or saving the page is up to you.{contact}</p>"""
    return layout(s, "Privacy", body)


def terms(s: Settings) -> str:
    src = f' (<a href="{esc(s.source_url)}" rel="noopener">source code</a>)' if s.source_url else ""
    body = f"""<h1>Terms of use</h1>
<ul>
<li>The site is free to use. It is provided as is, without warranty.</li>
<li>Astrological results are for guidance only. Please consult a qualified astrologer before making decisions.
Results depend on the accuracy of the birth time and place you enter.</li>
<li>Don't use automated tools to send large numbers of requests.</li>
<li>The software is licensed under the GNU Affero General Public License v3{src}.</li>
</ul>"""
    return layout(s, "Terms", body)


def error_page(s: Settings, title: str, message: str, status_hint: str = "") -> str:
    body = f'<h1>{esc(title)}</h1><p>{esc(message)}</p><p>{esc(status_hint)}</p><p><a href="/">Home</a></p>'
    return layout(s, title, body)


# ------------------------------------------------------------------ Learn section
def learn_index(s: Settings) -> str:
    cards = "".join(f'<a class="card" href="/learn/{a.slug}"><h2>{esc(a.title)}</h2><p>{esc(a.summary)}</p></a>'
                    for a in ARTICLES)
    body = (f'<h1>Learn</h1><p class="lead">Short guides to the charts and matching methods used on {esc(s.site_name)}.'
            f'</p><div class="cards">{cards}</div>')
    return layout(s, "Learn", body, active="learn")


def learn_article(s: Settings, a: Article) -> str:
    others = "".join(f'<li><a href="/learn/{o.slug}">{esc(o.title)}</a></li>' for o in ARTICLES if o.slug != a.slug)
    body = (f'<article class="article"><p class="crumb"><a href="/learn">Learn</a></p><h1>{esc(a.title)}</h1>'
            f'<p class="lead">{esc(a.summary)}</p>{a.body}'
            f'<p class="cta"><a class="button primary" href="/horoscope">Make a horoscope</a> '
            f'<a class="button" href="/match">Check matching</a></p>'
            f'<p class="small">For guidance only. Please consult an astrologer before taking decisions.</p>'
            f'<h2>More guides</h2><ul>{others}</ul></article>')
    return layout(s, a.title, body, active="learn")
