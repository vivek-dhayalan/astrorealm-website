"""HTML for the website, built with plain functions (no template engine).

Every user-supplied value goes through esc(); the only raw HTML inserted is the sanitized
description and SVGs we render ourselves.
"""
from __future__ import annotations

import contextvars
import json
from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from ..core.reference import NAKSHATRAS, RASHIS
from ..render import i18n
from . import learn_hi, learn_kn, learn_ml, learn_ta, learn_te
from .learn import ARTICLES, MODIFIED, PUBLISHED, Article
from .forms import CHART_PARTS, BirthInput, HoroscopeForm, MatchForm
from .settings import Settings
from .strings import LANG_NAMES, LANGS, t
from .form_text import TIPS as FORM_TIPS, ft
from .ui import LANG_LABEL, SITE_LANGS, T, credit_use, localize_links, lpath, page_meta, pick
from . import ui as _ui

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
STATIC_VERSION = "10"


def esc(v) -> str:
    return escape("" if v is None else str(v), quote=True)


# ------------------------------------------------------------------ SEO
DEFAULT_DESC = ("Free horoscope (jathagam) and marriage matching — Porutham and Ashtakoota (Guna Milan) — "
                "in English, Tamil, Telugu, Malayalam, Kannada and Hindi.")
OG_LOCALE = {"en": "en_IN", "ta": "ta_IN", "hi": "hi_IN", "te": "te_IN", "ml": "ml_IN", "kn": "kn_IN"}
ARTICLES_BY_LANG = {"en": ARTICLES, "ta": learn_ta.ARTICLES, "hi": learn_hi.ARTICLES, "te": learn_te.ARTICLES,
                    "ml": learn_ml.ARTICLES, "kn": learn_kn.ARTICLES}


def site_lang(lang: str | None) -> str:
    return lang if lang in SITE_LANGS else "en"


def meta(s: Settings, key: str, lang: str = "en") -> dict:
    title, desc = page_meta(key, site_lang(lang))
    return {"page_title": title.format(site=s.site_name), "description": desc.format(site=s.site_name)}


def lang_switch(current: str, path: str) -> str:
    """Language menu: a dropdown of links to the same page in each site language. Plain links (not a <select>), so it
    works without JavaScript and search engines can follow them. hreflang comes before href so localize_links leaves
    these alone."""
    items = "".join(
        f'<li><a hreflang="{code}" href="{lpath(code, path)}" lang="{code}"'
        f'{" aria-current=" + chr(34) + "true" + chr(34) if code == current else ""}>{LANG_LABEL[code]}</a></li>'
        for code in SITE_LANGS)
    return (f'<details class="hmenu lang-menu"><summary aria-label="{esc(T(current, "language"))}: {LANG_LABEL[current]}">'
            f'<span class="globe" aria-hidden="true"></span>{LANG_LABEL[current]}</summary>'
            f'<ul>{items}</ul></details>')


THEME_ICONS = {
    "auto": '<svg class="ticon t-auto" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6"/>'
            '<path class="fill" d="M8 2a6 6 0 0 1 0 12z"/></svg>',
    "light": '<svg class="ticon t-light" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="3"/>'
             '<path d="M8 1v2M8 13v2M1 8h2M13 8h2M3 3l1.4 1.4M11.6 11.6 13 13M3 13l1.4-1.4M11.6 4.4 13 3"/></svg>',
    "dark": '<svg class="ticon t-dark" viewBox="0 0 16 16" aria-hidden="true">'
            '<path d="M13.5 10.2A6 6 0 0 1 5.8 2.5a6 6 0 1 0 7.7 7.7z"/></svg>',
}
# Set before the page paints, so a saved choice never flashes the other theme first
THEME_BOOT = ('<script>try{var t=localStorage.getItem("theme");if(t==="light"||t==="dark")'
              'document.documentElement.setAttribute("data-theme",t)}catch(e){}</script>')


# Language on arrival: a choice made in the language menu is remembered and wins; otherwise, on an English page, the
# browser's first (main) language picks Tamil or Hindi. Any other browser language — including ones the site doesn't
# have yet, such as Telugu — stays on English. Search-engine crawlers send English and keep no storage, so every
# language version stays crawlable at its own address.
_LANGS_JS = ",".join(f'"{c}"' for c in SITE_LANGS)
_PREFIX_RE = "|".join(c for c in SITE_LANGS if c != "en")
LANG_BOOT = ('<script>(function(){try{var L=[' + _LANGS_JS + '],c=document.documentElement.lang,'
             'p=localStorage.getItem("lang"),w=L.indexOf(p)>=0?p:"";'
             'if(!w&&c==="en"){var n=(navigator.languages&&navigator.languages[0])||navigator.language||"",'
             'b=String(n).toLowerCase().split("-")[0];if(L.indexOf(b)>=0)w=b}'
             'if(w&&w!==c){var r=location.pathname.replace(/^\\/(' + _PREFIX_RE + ')(?=\\/|$)/,"")||"/";'
             'location.replace((w==="en"?r:"/"+w+(r==="/"?"":r))+location.search+location.hash)}}catch(e){}})()</script>')


def theme_menu(lang: str) -> str:
    """Theme: follow the device (default), light or dark. The choice is remembered in this browser only."""
    items = "".join(f'<li><button type="button" role="menuitemradio" aria-checked="{"true" if k == "auto" else "false"}" '
                    f'data-action="theme" data-theme="{k}">{THEME_ICONS[k]}{esc(T(lang, "theme_" + k))}</button></li>'
                    for k in ("auto", "light", "dark"))
    label = esc(T(lang, "theme"))
    return (f'<details class="hmenu theme-menu"><summary aria-label="{label}" title="{label}">'
            f'{"".join(THEME_ICONS.values())}</summary><ul role="menu">{items}</ul></details>')


def abs_url(s: Settings, path: str) -> str:
    return f"{s.base_url.rstrip('/')}{path}" if s.base_url else path


def jsonld(data) -> str:
    """JSON-LD block; '<' is escaped so the data can never close the script element."""
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    return f'<script type="application/ld+json">{text}</script>'


def org_ld(s: Settings) -> dict:
    return {"@type": "Organization", "name": s.site_name, "url": abs_url(s, "/")}


def breadcrumb_ld(s: Settings, trail: list[tuple[str, str]]) -> dict:
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": name, "item": abs_url(s, path)}
                                for i, (name, path) in enumerate(trail)]}


def article_ld(s: Settings, path: str, headline: str, description: str, lang: str = "en") -> dict:
    return {"@context": "https://schema.org", "@type": "Article", "headline": headline[:110],
            "description": description, "inLanguage": lang, "url": abs_url(s, path),
            "mainEntityOfPage": abs_url(s, path), "datePublished": PUBLISHED, "dateModified": MODIFIED,
            "author": org_ld(s), "publisher": org_ld(s)}


def app_ld(s: Settings, path: str, name: str, description: str) -> dict:
    return {"@context": "https://schema.org", "@type": "WebApplication", "name": name, "url": abs_url(s, path),
            "description": description, "applicationCategory": "LifestyleApplication", "operatingSystem": "Any",
            "isAccessibleForFree": True, "inLanguage": ["en", "ta", "te", "ml", "kn", "hi"],
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "INR"}, "provider": org_ld(s)}


def seo_head(s: Settings, full_title: str, description: str, path: str | None, lang: str,
             alternates: dict[str, str] | None, ld: list | None, og_type: str) -> str:
    out = [f'<meta name="description" content="{esc(description)}">']
    if path is not None and s.base_url:
        url = abs_url(s, path)
        out.append(f'<link rel="canonical" href="{esc(url)}">')
        if alternates:
            for code, alt in alternates.items():
                out.append(f'<link rel="alternate" hreflang="{code}" href="{esc(abs_url(s, alt))}">')
            if "en" in alternates:
                out.append(f'<link rel="alternate" hreflang="x-default" href="{esc(abs_url(s, alternates["en"]))}">')
        out += [f'<meta property="og:url" content="{esc(url)}">',
                f'<meta property="og:type" content="{og_type}">',
                f'<meta property="og:site_name" content="{esc(s.site_name)}">',
                f'<meta property="og:title" content="{esc(full_title)}">',
                f'<meta property="og:description" content="{esc(description)}">',
                f'<meta property="og:locale" content="{OG_LOCALE.get(lang, "en_IN")}">']
        for code in (alternates or {}):
            if code != lang:
                out.append(f'<meta property="og:locale:alternate" content="{OG_LOCALE.get(code, "en_IN")}">')
        if s.og_image_url:
            out.append(f'<meta property="og:image" content="{esc(s.og_image_url)}">')
        out.append(f'<meta name="twitter:card" content="{"summary_large_image" if s.og_image_url else "summary"}">')
    for item in ld or []:
        out.append(jsonld(item))
    return "\n".join(out)


# ------------------------------------------------------------------ layout pieces
def ad_slot(s: Settings, slot_id: str, kind: str) -> str:
    if s.ads_enabled and slot_id:
        return (f'<aside class="ad ad-{kind} no-print" aria-label="Advertisement">'
                f'<ins class="adsbygoogle" style="display:block" data-ad-client="{esc(s.adsense_client)}" '
                f'data-ad-slot="{esc(slot_id)}" data-ad-format="auto" data-full-width-responsive="true"></ins>'
                f'<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script></aside>')
    return ""  # no AdSense configured for this slot: no space is reserved


def layout(s: Settings, title: str, body: str, *, active: str = "", map_page: bool = False,
           turnstile: bool = False, side_ad: bool = True, ads: bool = True, path: str | None = None,
           description: str | None = None, page_title: str | None = None, lang: str = "en",
           ld: list | None = None, og_type: str = "website") -> str:
    """ads=False for result pages: they hold names and birth details, so no ad or analytics script runs there.
    path: the page's language-neutral path (/learn/x) — gives the canonical link, the hreflang links and the language
    switch (None on result and error pages). lang: the site language (en, ta, hi); internal links follow it.
    page_title: the full <title>; default "<title> · <site name>"."""
    lang = site_lang(lang)
    full_title = page_title or f"{title} · {s.site_name}"
    alternates = {code: lpath(code, path) for code in SITE_LANGS} if path is not None else None
    switch = lang_switch(lang, path) if path is not None else ""
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
        for key, href, label in (("horoscope", "/horoscope", T(lang, "nav_horoscope")),
                                 ("match", "/match", T(lang, "nav_match")), ("learn", "/learn", T(lang, "nav_learn")),
                                 ("credits", "/credits", T(lang, "nav_credits"))))
    consent = ""
    if ads_on or ga_on:
        what = T(lang, "and").join(T(lang, k) for k, on in (("consent_ads", ads_on), ("consent_ga", ga_on)) if on)
        consent = (f'<div class="consent no-print" id="consent" hidden><p>{esc(T(lang, "consent", what=what))} '
                   f'<a href="/privacy">{T(lang, "foot_privacy")}</a></p>'
                   '<button type="button" data-action="consent-ok">OK</button></div>')
    side = ad_slot(s, s.adsense_slot_side, "side") if (side_ad and ads) else ""
    top = ad_slot(s, s.adsense_slot_top, "top") if ads else ""
    bottom = ad_slot(s, s.adsense_slot_bottom, "bottom") if ads else ""
    page = f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{THEME_BOOT}{LANG_BOOT if path is not None else ""}
<title>{esc(full_title)}</title>
{seo_head(s, full_title, description or DEFAULT_DESC, lpath(lang, path) if path is not None else None, lang,
          alternates, ld, og_type)}
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS_URL}">
<link rel="stylesheet" href="/static/site.css?v={STATIC_VERSION}">
{''.join(head_extra)}
</head>
<body data-map-style="{esc(s.map_style_url)}" data-t-near="{esc(ft(lang, "Near"))}" data-t-pinned="{esc(ft(lang, "Pinned location"))}">
<a class="skip" href="#main">{T(lang, "skip")}</a>
<header class="site-head no-print"><a class="brand" href="/">{esc(s.site_name)}</a><nav>{nav}</nav>
<div class="head-tools">{switch}{theme_menu(lang)}</div></header>
{top}
<div class="page{' with-side' if side else ''}">
<main id="main">{body}</main>
{side}
</div>
{bottom}
<footer class="site-foot no-print">
<p>{T(lang, "foot_disclaimer")}</p>
<p><a href="/learn">{T(lang, "nav_learn")}</a> · <a href="/privacy">{T(lang, "foot_privacy")}</a> · <a href="/terms">{T(lang, "foot_terms")}</a> · <a href="/credits">{T(lang, "nav_credits")}</a> · <a href="/upcoming">{T(lang, "foot_upcoming")}</a></p>
<p class="small">{T(lang, "foot_attrib", geonames='<a href="https://www.geonames.org/" rel="noopener">GeoNames</a>')}</p>
</footer>
{consent}
{MAP_JS if map_page else ''}
<script src="/static/site.js?v={STATIC_VERSION}" defer></script>
</body>
</html>"""
    return localize_links(page, lang)


# ------------------------------------------------------------------ form widgets
_FORM_LANG: contextvars.ContextVar[str] = contextvars.ContextVar("form_lang", default="en")


def L(text: str) -> str:
    """Form text in the language of the form being drawn."""
    return ft(_FORM_LANG.get(), text)


def _err(errors: dict, key: str) -> str:
    return f'<p class="err" id="{esc(key)}-err">{esc(L(errors[key]))}</p>' if key in errors else ""


def _aria(errors: dict, key: str) -> str:
    return f' aria-invalid="true" aria-describedby="{esc(key)}-err"' if key in errors else ""


def text_field(key: str, label: str, value: str, errors: dict, *, type_: str = "text", required: bool = False,
               maxlength: int = 80, hint: str = "", extra: str = "") -> str:
    req = " required" if required else ""
    h = f'<p class="hint">{esc(L(hint))}</p>' if hint else ""
    return (f'<div class="field"><label for="{key}">{esc(L(label))}{" *" if required else ""}</label>'
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
                  "with the KP ayanamsa. Prints as a separate page.", "/learn/kp-astrology"),
}


def tip(key: str) -> str:
    """Info button with a small popover (hover, focus or tap). Text is ours, never user input."""
    title, text, href = TIPS[key]
    lang = _FORM_LANG.get()
    if lang in FORM_TIPS.get(key, {}):
        title, text = FORM_TIPS[key][lang]
    tid = f"tip-{key.lower()}"
    return (f'<span class="tip"><button type="button" class="tip-btn" aria-expanded="false" aria-controls="{tid}" '
            f'aria-label="{esc(title)}" data-action="tip">i</button>'
            f'<span class="tip-box" id="{tid}" role="note"><b>{esc(title)}</b> {esc(text)} '
            f'<a href="{href}" target="_blank" rel="noopener">{esc(L("Learn more"))}</a></span></span>')


def select_field(key: str, label: str, value: str, options: list[tuple[str, str]], errors: dict,
                 required: bool = False, blank: str | None = None, info: str = "") -> str:
    opts = f'<option value="">{esc(L(blank))}</option>' if blank is not None else ""
    opts += "".join(f'<option value="{esc(v)}"{" selected" if v == value else ""}>{esc(L(lbl))}</option>'
                    for v, lbl in options)
    lab = f'<label for="{key}">{esc(L(label))}{" *" if required else ""}</label>'
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
<label for="{key}">{esc(L("Place of birth"))} *</label>
<div class="place-box">
<input id="{key}" name="{key}" type="text" value="{esc(b.place)}" maxlength="120" autocomplete="off"
 placeholder="{esc(L("Start typing a town or city"))}" role="combobox" aria-autocomplete="list" aria-expanded="false"
 aria-controls="{key}-list"{_aria(errors, key)}>
<ul class="suggest" id="{key}-list" role="listbox" hidden></ul>
</div>
<input type="hidden" name="{prefix}lat" value="{lat}"><input type="hidden" name="{prefix}lon" value="{lon}">
<p class="hint"><button type="button" class="linkish" data-action="map">{esc(L("Pick on map"))}</button>
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
    return f'<p class="hint no-print">{esc(L("Bot check is off (local development)."))}</p>'


def banner(message: str | None, candidates: list[dict] | None = None) -> str:
    if not message:
        return ""
    extra = ""
    if candidates:
        items = "".join(f"<li>{esc(c.get('name'))}, {esc(c.get('admin1') or '')} {esc(c.get('countryName') or '')}</li>"
                        for c in candidates)
        extra = f"<p>{esc(L('Pick one from the suggestions as you type, or use the map. Matches:'))}</p><ul>{items}</ul>"
    return f'<div class="banner" role="alert"><p>{esc(L(message))}</p>{extra}</div>'


# ------------------------------------------------------------------ pages
def home(s: Settings, lang: str = "en") -> str:
    from .stars import NAK_SLUGS, RASI_SLUGS, names
    lang = site_lang(lang)
    stars = "".join(f'<li><a href="/learn/nakshatra/{NAK_SLUGS[i]}">{esc(names(lang, "nakshatra", i))}</a></li>'
                    for i in range(27))
    rasis = "".join(f'<li><a href="/learn/rasi/{RASI_SLUGS[i]}">{esc(names(lang, "rashi", i))}</a></li>'
                    for i in range(12))
    cards = "".join(f'<a class="card" href="{href}"><h2>{esc(T(lang, k))}</h2><p>{esc(T(lang, k + "_desc"))}</p></a>'
                    for href, k in (("/horoscope", "card_h"), ("/match", "card_m"),
                                    ("/learn/nakshatra-porutham-table", "card_table"), ("/learn", "card_learn")))
    body = f"""<section class="hero"><h1>{esc(T(lang, "home_h1"))}</h1>
<p>{esc(T(lang, "home_intro"))}</p></section>
<div class="cards">{cards}</div>
<h2><a href="/learn/nakshatras">{esc(T(lang, "stars_h"))}</a></h2>
<p>{esc(T(lang, "stars_intro"))}</p>
<ol class="star-list">{stars}</ol>
<h2><a href="/learn/rasis">{esc(T(lang, "rasis_h"))}</a></h2>
<ol class="star-list">{rasis}</ol>"""
    m = meta(s, "home", lang)
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": s.site_name, "url": abs_url(s, lpath(lang, "/")),
           "description": m["description"], "inLanguage": lang},
          {"@context": "https://schema.org", **org_ld(s)}]
    return layout(s, T(lang, "home_h1"), body, active="", path="/", lang=lang, ld=ld, **m)


def ui_field(lang: str) -> str:
    """Hidden field carrying the site language through the POST, so the result page keeps it."""
    return f'<input type="hidden" name="ui" value="{esc(site_lang(lang))}">'


def form_note(lang: str) -> str:
    return ""  # forms are in the page language now


def horoscope_form(s: Settings, frm: HoroscopeForm, message: str | None = None,
                   candidates: list[dict] | None = None, ui: str = "en") -> str:
    ui = site_lang(ui)
    token = _FORM_LANG.set(ui)
    try:
        return _horoscope_form(s, frm, message, candidates, ui)
    finally:
        _FORM_LANG.reset(token)


def _horoscope_form(s: Settings, frm: HoroscopeForm, message, candidates, ui: str) -> str:
    e = frm.errors
    b = frm.birth
    parts = "".join(
        f'<span class="check-wrap"><label class="check"><input type="checkbox" name="parts" value="{p}"'
        f'{" checked" if p in frm.parts else ""}> {esc(L(lbl))}</label>{tip(p)}</span>'
        for p, lbl in zip(CHART_PARTS, ("Rasi chart", "Navamsa chart", "KP planet & cusp tables")))
    num = lambda k, lbl: text_field(k, lbl, "" if getattr(frm, k) is None else str(getattr(frm, k)), e,  # noqa: E731
                                    type_="number", maxlength=2, extra=' min="0" max="20" inputmode="numeric"')
    living = [("living", "Living"), ("deceased", "Deceased")]
    body = f"""<h1>{esc(T(ui, "hform_h1"))}</h1>
<p class="lead">{esc(T(ui, "hform_lead"))}</p>{form_note(ui)}
{banner(message, candidates)}
<form method="post" action="/horoscope" class="form" novalidate>{ui_field(ui)}
<fieldset><legend>{L("Birth details")}</legend>
{birth_fields("", b, e, with_sex=True)}
</fieldset>
<fieldset><legend>{L("Chart options")}</legend>
{common_options(frm.lang, frm.ayanamsa.value, e)}
<div class="field"><span class="label">{L("Include")}</span><div class="checks">{parts}</div>{_err(e, "parts")}</div>
</fieldset>
<fieldset><legend>{L("Family")}</legend>
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
<fieldset><legend>{L("Personal details")}</legend>
<div class="row2">
{text_field("degree", "Education — degree", frm.degree, e, maxlength=80)}
{text_field("branch", "Education — branch / specialisation", frm.branch, e, maxlength=80)}
</div>
<div class="row2">
{text_field("occupation", "Work / occupation", frm.occupation, e, maxlength=120)}
{text_field("complexion", "Complexion (optional)", frm.complexion, e, maxlength=40)}
</div>
<div class="field"><label id="desc-label">{L("About (any language)")}</label>
<div class="rte">
<div class="rte-bar" role="toolbar" aria-label="{L("Formatting")}">
<button type="button" data-cmd="bold" title="{L("Bold")}"><b>B</b></button>
<button type="button" data-cmd="italic" title="{L("Italic")}"><i>I</i></button>
<button type="button" data-cmd="underline" title="{L("Underline")}"><u>U</u></button>
<button type="button" data-cmd="insertUnorderedList" title="{L("Bulleted list")}">• {L("List")}</button>
<button type="button" data-cmd="insertOrderedList" title="{L("Numbered list")}">1. {L("List")}</button>
</div>
<div class="rte-area" contenteditable="true" role="textbox" aria-multiline="true" aria-labelledby="desc-label">{frm.description}</div>
<textarea name="description" hidden>{esc(frm.description)}</textarea>
</div>
<p class="hint">{L("Up to about 4,000 characters. Type in any language.")}</p>
</div>
</fieldset>
{turnstile_widget(s)}
<p><button type="submit" class="primary">{L("Generate horoscope")}</button></p>
</form>"""
    m = meta(s, "horoscope", ui)
    return layout(s, T(ui, "nav_horoscope"), body, active="horoscope", map_page=True, turnstile=True,
                  path="/horoscope", lang=ui, **m,
                  ld=[app_ld(s, lpath(ui, "/horoscope"), f"{s.site_name} horoscope generator", m["description"])])


def match_form(s: Settings, frm: MatchForm, message: str | None = None,
               candidates: list[dict] | None = None, ui: str = "en") -> str:
    ui = site_lang(ui)
    token = _FORM_LANG.set(ui)
    try:
        return _match_form(s, frm, message, candidates, ui)
    finally:
        _FORM_LANG.reset(token)


def _match_form(s: Settings, frm: MatchForm, message, candidates, ui: str) -> str:
    e = frm.errors
    body = f"""<h1>{esc(T(ui, "mform_h1"))}</h1>
<p class="lead">{T(ui, "mform_lead")}</p>{form_note(ui)}
{banner(message, candidates)}
<form method="post" action="/match" class="form" novalidate>{ui_field(ui)}
<div class="pair-form">
<fieldset class="bride"><legend>{L("Bride")}</legend>{birth_fields("b_", frm.bride, e, with_sex=False)}</fieldset>
<fieldset class="groom"><legend>{L("Groom")}</legend>{birth_fields("g_", frm.groom, e, with_sex=False)}</fieldset>
</div>
<fieldset><legend>{L("Options")}</legend>{common_options(frm.lang, frm.ayanamsa.value, e)}</fieldset>
{turnstile_widget(s)}
<p><button type="submit" class="primary">{L("Check matching")}</button></p>
</form>"""
    m = meta(s, "match", ui)
    return layout(s, T(ui, "nav_match"), body, active="match", map_page=True, turnstile=True, path="/match",
                  lang=ui, **m,
                  ld=[app_ld(s, lpath(ui, "/match"), f"{s.site_name} marriage matching", m["description"])])


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


def toolbar(back: str, ui: str = "en") -> str:
    return (f'<div class="toolbar no-print"><button type="button" class="primary" data-action="print">'
            f'{esc(T(ui, "print"))}</button><button type="button" data-action="back">{esc(T(ui, "edit"))}</button>'
            f'<a href="{back}">{esc(T(ui, "again"))}</a><span class="hint">{esc(T(ui, "print_hint"))}</span></div>')


def horoscope_result(s: Settings, frm: HoroscopeForm, place_label: str, chart, svgs: dict[str, str],
                     ui: str = "en") -> str:
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
    body = toolbar("/horoscope", ui) + f'<div class="sheets" lang="{lang}">{"".join(sheets)}</div>'
    # generic title: names must not reach browser history, tab sync or any third-party script
    return layout(s, T(ui, "res_h"), body, active="horoscope", side_ad=False, ads=False, lang=ui)


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
                 ashta: dict, poru: dict, ui: str = "en") -> str:
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
    body = toolbar("/match", ui) + f'<div class="sheets" lang="{lang}">{sheets}</div>'
    return layout(s, T(ui, "res_m"), body, active="match", side_ad=False, ads=False, lang=ui)


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


def credits(s: Settings, lang: str = "en") -> str:
    lang = site_lang(lang)

    def use(text: str) -> str:
        return credit_use(lang, text)
    rows = "".join(f'<tr><th><a href="{esc(u)}" rel="noopener">{esc(n)}</a></th><td>{esc(lic)}</td><td>{esc(use(x))}</td></tr>'
                   for n, u, lic, x in CREDITS)
    src = (f'<p>{esc(T(lang, "agpl"))} <a href="{esc(s.source_url)}" rel="noopener">{esc(T(lang, "get_source"))}</a>.</p>'
           if s.source_url else f'<p>{esc(T(lang, "agpl"))}</p>')
    body = f"""<h1>{esc(T(lang, "credits_h1"))}</h1>{src}
<p>{esc(T(lang, "thanks"))}</p>
<div class="scroll"><table class="grid credits"><thead><tr><th>{esc(T(lang, "col_project"))}</th><th>{esc(T(lang, "col_licence"))}</th>
<th>{esc(T(lang, "col_use"))}</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="small">{T(lang, "rules_note", code="<code>app/rules/v1.py</code>")}</p>"""
    return layout(s, T(lang, "credits_h1"), body, active="credits", path="/credits", lang=lang,
                  **meta(s, "credits", lang))


# privacy text: key → (en, ta, hi); {link} and {contact} are filled in below
_PRIVACY = {
    "h1": ("Privacy", "தனியுரிமை", "गोपनीयता"),
    "intro": (
        "<b>We don't keep what you enter.</b> Names, birth details, family details and descriptions are used only to "
        "build the page you asked for, then discarded. They are not stored, logged or sent to advertisers.",
        "<b>நீங்கள் உள்ளிடுவதை நாங்கள் வைத்துக்கொள்வதில்லை.</b> பெயர்கள், பிறப்பு விவரங்கள், குடும்ப விவரங்கள், "
        "விவரணைகள் நீங்கள் கேட்ட பக்கத்தை உருவாக்க மட்டுமே பயன்படுத்தப்பட்டு, பின் நீக்கப்படுகின்றன. அவை "
        "சேமிக்கப்படுவதோ பதிவு செய்யப்படுவதோ விளம்பரதாரர்களுக்கு அனுப்பப்படுவதோ இல்லை.",
        "<b>आपकी दी हुई जानकारी हम नहीं रखते।</b> नाम, जन्म विवरण, परिवार का विवरण और परिचय केवल आपका माँगा हुआ "
        "पृष्ठ बनाने के लिए इस्तेमाल होते हैं, फिर हटा दिए जाते हैं। इन्हें न सहेजा जाता है, न लॉग किया जाता है, न "
        "विज्ञापनदाताओं को भेजा जाता है।"),
    "h_processed": ("What is processed", "எவை செயலாக்கப்படுகின்றன", "क्या प्रोसेस होता है"),
    "p_form": ("Your form entries — only while your page is generated.",
               "நீங்கள் படிவத்தில் உள்ளிடுபவை — உங்கள் பக்கம் உருவாக்கப்படும் நேரத்தில் மட்டும்.",
               "फ़ॉर्म में भरी जानकारी — केवल आपका पृष्ठ बनते समय।"),
    "p_ip": ("Your IP address — briefly, in memory, to limit abuse (too many requests).",
             "உங்கள் IP முகவரி — துஷ்பிரயோகத்தை (அதிகப்படியான கோரிக்கைகள்) தடுக்க, சிறிது நேரம், நினைவகத்தில் மட்டும்.",
             "आपका IP पता — दुरुपयोग (बहुत अधिक अनुरोध) रोकने के लिए, थोड़ी देर, केवल मेमोरी में।"),
    "p_place": ("Place search — the letters you type are sent to our own server to suggest places.",
                "இடத் தேடல் — நீங்கள் தட்டச்சு செய்யும் எழுத்துகள் இடங்களைப் பரிந்துரைக்க எங்கள் சேவையகத்துக்கு "
                "மட்டுமே அனுப்பப்படுகின்றன.",
                "स्थान खोज — आपके टाइप किए अक्षर स्थान सुझाने के लिए केवल हमारे अपने सर्वर पर भेजे जाते हैं।"),
    "h_third": ("Third parties", "மூன்றாம் தரப்பினர்", "तृतीय पक्ष"),
    "t_cloud": ("<b>Google Cloud</b> (Cloud Run and Firebase Hosting, Mumbai region) hosts the site.",
                "<b>Google Cloud</b> (Cloud Run, Firebase Hosting, மும்பை மண்டலம்) இந்தத் தளத்தை இயக்குகிறது.",
                "<b>Google Cloud</b> (Cloud Run और Firebase Hosting, मुंबई क्षेत्र) साइट को होस्ट करता है।"),
    "t_cf": ("<b>Cloudflare</b> runs the Turnstile bot check on the forms.",
             "<b>Cloudflare</b> படிவங்களில் Turnstile பாதுகாப்புச் சோதனையை இயக்குகிறது.",
             "<b>Cloudflare</b> फ़ॉर्म पर Turnstile बॉट जाँच चलाता है।"),
    "t_ads": ("<b>Google AdSense</b> shows ads and uses cookies for that. You can manage ad personalisation at {link}.",
              "<b>Google AdSense</b> விளம்பரங்களைக் காட்டுகிறது; அதற்காகக் குக்கீகளைப் பயன்படுத்துகிறது. விளம்பரத் "
              "தனிப்பயனாக்கத்தை {link}-இல் மாற்றலாம்.",
              "<b>Google AdSense</b> विज्ञापन दिखाता है और इसके लिए कुकीज़ इस्तेमाल करता है। विज्ञापन वैयक्तिकरण {link} "
              "पर बदल सकते हैं।"),
    "t_ga": ("<b>Google Analytics</b> counts visits to our pages (which pages, roughly where from, which device) using "
             "cookies. It does not run on the pages that show your horoscope or matching result. You can opt out with "
             "{link}.",
             "<b>Google Analytics</b> குக்கீகளைக் கொண்டு எங்கள் பக்கங்களுக்கான வருகைகளைக் கணக்கிடுகிறது (எந்தப் "
             "பக்கங்கள், தோராயமாக எங்கிருந்து, எந்தச் சாதனம்). உங்கள் ஜாதகம் அல்லது பொருத்த முடிவைக் காட்டும் "
             "பக்கங்களில் இது இயங்காது. {link} மூலம் விலகலாம்.",
             "<b>Google Analytics</b> कुकीज़ से हमारे पृष्ठों पर विज़िट गिनता है (कौन-से पृष्ठ, मोटे तौर पर कहाँ से, "
             "कौन-सा डिवाइस)। यह आपकी कुंडली या मिलान परिणाम वाले पृष्ठों पर नहीं चलता। {link} से बाहर हो सकते हैं।"),
    "ga_optout": ("Google's opt-out add-on", "Google-இன் விலகல் நீட்சி", "Google के ऑप्ट-आउट ऐड-ऑन"),
    "t_fonts": ("<b>Google Fonts</b> and <b>unpkg</b> serve fonts and the map library; <b>OpenFreeMap</b> serves the map "
                "images when you use “Pick on map”.",
                "<b>Google Fonts</b>, <b>unpkg</b> எழுத்துருக்களையும் வரைபட நிரலகத்தையும் வழங்குகின்றன; “வரைபடத்தில் "
                "தேர்வு” பயன்படுத்தும்போது <b>OpenFreeMap</b> வரைபடப் படங்களை வழங்குகிறது.",
                "<b>Google Fonts</b> और <b>unpkg</b> फ़ॉन्ट और मानचित्र लाइब्रेरी देते हैं; “मानचित्र पर चुनें” इस्तेमाल "
                "करने पर <b>OpenFreeMap</b> मानचित्र चित्र देता है।"),
    "none_get": ("None of them receive your form entries. Pages that show your horoscope or matching result carry no "
                 "ads or analytics.",
                 "இவர்கள் யாருக்கும் உங்கள் படிவ விவரங்கள் கிடைப்பதில்லை. உங்கள் ஜாதகம் அல்லது பொருத்த முடிவைக் "
                 "காட்டும் பக்கங்களில் விளம்பரங்களோ பகுப்பாய்வோ இல்லை.",
                 "इनमें से किसी को आपकी फ़ॉर्म जानकारी नहीं मिलती। आपकी कुंडली या मिलान परिणाम दिखाने वाले पृष्ठों पर "
                 "कोई विज्ञापन या एनालिटिक्स नहीं होता।"),
    "h_choices": ("Your choices", "உங்கள் தேர்வுகள்", "आपके विकल्प"),
    "choices": ("Because nothing is stored, there is nothing to delete. Printing or saving the page is up to you.",
                "எதுவும் சேமிக்கப்படாததால் நீக்க வேண்டியதும் எதுவுமில்லை. பக்கத்தை அச்சிடுவதும் சேமிப்பதும் உங்கள் "
                "விருப்பம்.",
                "कुछ भी सहेजा नहीं जाता, इसलिए हटाने को कुछ नहीं है। पृष्ठ प्रिंट करना या सहेजना आपकी मर्ज़ी है।"),
    "remember": (" Your language and theme choices are remembered in your own browser only.",
                 " நீங்கள் தேர்ந்தெடுக்கும் மொழியும் தோற்றமும் உங்கள் உலாவியில் மட்டுமே நினைவில் வைக்கப்படுகின்றன.",
                 " आपकी चुनी हुई भाषा और थीम केवल आपके अपने ब्राउज़र में याद रखी जाती हैं।"),
    "write": ("Write to {email}.", "தொடர்புக்கு: {email}.", "संपर्क: {email}।"),
}


def privacy(s: Settings, lang: str = "en") -> str:
    lang = site_lang(lang)
    ex = _ui._extra(lang)
    P = lambda k: pick(_PRIVACY[k], lang, ex.PRIVACY if ex else None, k)  # noqa: E731  (our own text; has markup)
    contact = (" " + P("write").format(email=f'<a href="mailto:{esc(s.contact_email)}">{esc(s.contact_email)}</a>')
               if s.contact_email else "")
    # list only the services that are actually switched on
    ads_link = '<a href="https://adssettings.google.com/" rel="noopener">adssettings.google.com</a>'
    ads_li = f'<li>{P("t_ads").format(link=ads_link)}</li>' if s.ads_enabled else ""
    ga_link = f'<a href="https://tools.google.com/dlpage/gaoptout" rel="noopener">{P("ga_optout")}</a>'
    ga_li = f'<li>{P("t_ga").format(link=ga_link)}</li>' if s.analytics_enabled else ""
    body = f"""<h1>{P("h1")}</h1>
<p>{P("intro")}</p>
<h2>{P("h_processed")}</h2>
<ul><li>{P("p_form")}</li><li>{P("p_ip")}</li><li>{P("p_place")}</li></ul>
<h2>{P("h_third")}</h2>
<ul><li>{P("t_cloud")}</li><li>{P("t_cf")}</li>{ads_li}{ga_li}<li>{P("t_fonts")}</li></ul>
<p>{P("none_get")}</p>
<h2>{P("h_choices")}</h2>
<p>{P("choices")}{P("remember")}{contact}</p>"""
    return layout(s, P("h1"), body, path="/privacy", lang=lang, **meta(s, "privacy", lang))


_TERMS = [
    ("The site is free to use. It is provided as is, without warranty.",
     "இந்தத் தளம் இலவசம். எந்த உத்தரவாதமும் இன்றி உள்ளபடியே வழங்கப்படுகிறது.",
     "साइट का उपयोग मुफ़्त है। यह जैसी है वैसी दी जाती है, बिना किसी वारंटी के।"),
    ("Astrological results are for guidance only. Please consult a qualified astrologer before making decisions. "
     "Results depend on the accuracy of the birth time and place you enter.",
     "ஜோதிட முடிவுகள் வழிகாட்டுதலுக்கு மட்டுமே. முடிவெடுக்கும் முன் தகுதியான ஜோதிடரை அணுகவும். முடிவுகள் நீங்கள் "
     "உள்ளிடும் பிறந்த நேரம், இடத்தின் துல்லியத்தைப் பொறுத்தவை.",
     "ज्योतिषीय परिणाम केवल मार्गदर्शन के लिए हैं। निर्णय से पहले किसी योग्य ज्योतिषी से सलाह लें। परिणाम आपके दिए "
     "जन्म समय और स्थान की सटीकता पर निर्भर हैं।"),
    ("Don't use automated tools to send large numbers of requests.",
     "அதிக எண்ணிக்கையில் கோரிக்கைகளை அனுப்பத் தானியங்கிக் கருவிகளைப் பயன்படுத்த வேண்டாம்.",
     "बहुत सारे अनुरोध भेजने के लिए स्वचालित टूल का उपयोग न करें।"),
    ("The software is licensed under the GNU Affero General Public License v3{src}.",
     "இந்த மென்பொருள் GNU Affero General Public License v3 உரிமத்தின் கீழ் வழங்கப்படுகிறது{src}.",
     "सॉफ़्टवेयर GNU Affero General Public License v3 के तहत लाइसेंस प्राप्त है{src}।"),
]


def terms(s: Settings, lang: str = "en") -> str:
    lang = site_lang(lang)
    ex = _ui._extra(lang)
    src = (f' (<a href="{esc(s.source_url)}" rel="noopener">{esc(T(lang, "source_code"))}</a>)'
           if s.source_url else "")
    rows = [pick(row, lang) if not ex else ex.TERMS[n] for n, row in enumerate(_TERMS)]
    items = "".join(f"<li>{r.format(src=src) if '{src}' in r else r}</li>" for r in rows)
    body = f'<h1>{esc(T(lang, "terms_h1"))}</h1><ul>{items}</ul>'
    return layout(s, T(lang, "terms_h1"), body, path="/terms", lang=lang, **meta(s, "terms", lang))


def error_page(s: Settings, title: str, message: str, status_hint: str = "", lang: str = "en") -> str:
    body = (f'<h1>{esc(title)}</h1><p>{esc(message)}</p><p>{esc(status_hint)}</p>'
            f'<p><a href="/">{esc(T(lang, "home"))}</a></p>')
    return layout(s, title, body, lang=lang)


def not_found(s: Settings, lang: str = "en") -> str:
    return error_page(s, T(lang, "not_found"), T(lang, "no_page"), lang=lang)


# ------------------------------------------------------------------ roadmap
UPCOMING = [  # (status key, {lang: (title, description)})
    ("st_review", {
        "en": ("Manglik (Chevvai) dosham check",
               "Shows whether Mars causes dosham for the bride and the groom, and whether it is cancelled. The "
               "cancellation rules are being checked with an astrologer before this appears in matching."),
        "ta": ("செவ்வாய் தோஷம்",
               "மணமகள், மணமகன் ஜாதகங்களில் செவ்வாய் தோஷம் உள்ளதா, அது நிவர்த்தி ஆகிறதா என்பதைக் காட்டும். நிவர்த்தி "
               "விதிகள் ஜோதிடருடன் சரிபார்க்கப்பட்டு வருகின்றன."),
        "hi": ("मांगलिक दोष (मंगल दोष)",
               "वर और वधू की कुंडली में मंगल दोष है या नहीं, और क्या वह रद्द होता है — यह दिखाएगा। रद्द होने के नियम "
               "ज्योतिषी के साथ जाँचे जा रहे हैं।")}),
    ("st_review", {
        "en": ("KP 7th cusp analysis",
               "Marriage matching through the 7th house cusp in KP astrology: its sub-lord and the houses it signifies. "
               "Results are being compared with an astrologer's readings."),
        "ta": ("KP 7-ஆம் பாவ முனை ஆய்வு",
               "KP முறையில் 7-ஆம் பாவ முனையின் உப அதிபதி, அது குறிக்கும் பாவங்கள் மூலம் திருமணப் பொருத்தம். முடிவுகள் "
               "ஜோதிடரின் கணிப்புகளுடன் ஒப்பிடப்பட்டு வருகின்றன."),
        "hi": ("KP सप्तम भाव संधि विश्लेषण",
               "KP ज्योतिष में सप्तम भाव संधि (कस्प) के उप-स्वामी और उसके संकेतित भावों से विवाह मिलान। परिणाम "
               "ज्योतिषी की गणनाओं से मिलाए जा रहे हैं।")}),
    ("st_planned", {
        "en": ("KP Dasavidha Porutham",
               "The ten matching checks done the KP way, using star lords and sub-lords instead of the Moon's star "
               "alone."),
        "ta": ("KP தசவித பொருத்தம்",
               "சந்திரனின் நட்சத்திரம் மட்டுமின்றி நட்சத்திர அதிபதி, உப அதிபதிகளைக் கொண்டு KP முறையில் பத்துப் "
               "பொருத்தங்கள்."),
        "hi": ("KP दशविध पोरुथम",
               "केवल चंद्र नक्षत्र नहीं, बल्कि नक्षत्र स्वामी और उप-स्वामी से KP पद्धति के दस मिलान।")}),
    ("st_review", {
        "en": ("Better Telugu, Malayalam and Kannada",
               "The labels in these languages are being reviewed by native speakers."),
        "ta": ("தெலுங்கு, மலையாளம், கன்னடம் — மேம்பாடு",
               "இந்த மொழிகளிலுள்ள சொற்கள் அந்தந்த மொழி பேசுபவர்களால் சரிபார்க்கப்பட்டு வருகின்றன."),
        "hi": ("बेहतर तेलुगु, मलयालम और कन्नड़", "इन भाषाओं के शब्दों की समीक्षा मूल भाषी कर रहे हैं।")}),
    ("st_exploring", {
        "en": ("More matching methods",
               "Further checks astrologers use alongside Porutham and Ashtakoota, for example Papa Samyam (balance of "
               "malefic influence) and Dasa Sandhi (timing of major periods)."),
        "ta": ("மேலும் பொருத்த முறைகள்",
               "பொருத்தம், அஷ்டகூடத்துடன் ஜோதிடர்கள் பார்க்கும் பிற ஆய்வுகள் — எ.கா. பாப சாம்யம் (பாவ கிரகச் "
               "சமநிலை), தசா சந்தி (தசைகள் மாறும் காலம்)."),
        "hi": ("और मिलान पद्धतियाँ",
               "पोरुथम और अष्टकूट के साथ ज्योतिषी जो और जाँच करते हैं, जैसे पाप साम्य (पाप ग्रहों का संतुलन) और दशा "
               "संधि (महादशाओं का समय)।")}),
    ("st_exploring", {
        "en": ("Horoscope templates", "A choice of print layouts and designs for your horoscope, from traditional to "
               "modern."),
        "ta": ("ஜாதக வடிவமைப்புகள்", "பாரம்பரியத்திலிருந்து நவீனம் வரை, உங்கள் ஜாதகத்துக்குப் பல அச்சு வடிவமைப்புகள்."),
        "hi": ("कुंडली टेम्पलेट", "पारंपरिक से आधुनिक तक, आपकी कुंडली के लिए कई प्रिंट डिज़ाइन।")}),
    ("st_exploring", {
        "en": ("Share on WhatsApp and email",
               "Save your horoscope or matching result as a PDF and send it straight from your phone. Your details will "
               "still not be stored on our side."),
        "ta": ("WhatsApp, மின்னஞ்சலில் பகிர",
               "ஜாதகம் அல்லது பொருத்த முடிவை PDF ஆகச் சேமித்து உங்கள் கைப்பேசியிலிருந்தே அனுப்பலாம். அப்போதும் "
               "உங்கள் விவரங்கள் எங்களிடம் சேமிக்கப்படாது."),
        "hi": ("WhatsApp और ईमेल पर भेजें",
               "अपनी कुंडली या मिलान परिणाम PDF के रूप में सहेजकर सीधे अपने फ़ोन से भेजें। तब भी आपका विवरण हमारे पास "
               "सहेजा नहीं जाएगा।")}),
    ("st_exploring", {
        "en": ("AI assistant",
               "Ask questions about your chart or matching result in plain language and get them explained, in your "
               "language."),
        "ta": ("AI உதவியாளர்",
               "உங்கள் ஜாதகம் அல்லது பொருத்த முடிவு பற்றி எளிய மொழியில் கேள்வி கேட்டு, உங்கள் மொழியிலேயே விளக்கம் "
               "பெறலாம்."),
        "hi": ("AI सहायक", "अपनी कुंडली या मिलान परिणाम के बारे में सरल भाषा में सवाल पूछें और अपनी भाषा में जवाब पाएँ।")}),
]


def upcoming(s: Settings, lang: str = "en") -> str:
    lang = site_lang(lang)
    ex = _ui._extra(lang)

    def item(n: int, text: dict) -> tuple[str, str]:
        return text[lang] if lang in text else (ex.UPCOMING[n] if ex else text["en"])
    items = "".join(f'<li class="card"><span class="tag">{esc(T(lang, st))}</span><h2>{esc(item(n, text)[0])}</h2>'
                    f'<p>{esc(item(n, text)[1])}</p></li>' for n, (st, text) in enumerate(UPCOMING))
    body = (f'<h1>{esc(T(lang, "up_h1"))}</h1><p class="lead">{esc(T(lang, "up_lead", site=s.site_name))}</p>'
            f'<ul class="cards roadmap">{items}</ul>')
    return layout(s, T(lang, "up_h1"), body, path="/upcoming", lang=lang, **meta(s, "upcoming", lang))


# ------------------------------------------------------------------ Learn section
def learn_index(s: Settings, lang: str = "en") -> str:
    lang = site_lang(lang)
    cards = "".join(f'<a class="card" href="/learn/{a.slug}"><h2>{esc(a.title)}</h2><p>{esc(a.summary)}</p></a>'
                    for a in ARTICLES_BY_LANG[lang])
    ref = "".join(f'<a class="card" href="{href}"><h2>{esc(T(lang, title))}</h2><p>{esc(T(lang, desc))}</p></a>'
                  for href, title, desc in (("/learn/nakshatra-porutham-table", "card_table", "ref_table_desc"),
                                            ("/learn/nakshatras", "stars_h", "ref_naks_desc"),
                                            ("/learn/rasis", "rasis_h", "ref_rasis_desc")))
    body = (f'<h1>{esc(T(lang, "learn_h1"))}</h1><p class="lead">{esc(T(lang, "learn_lead", site=s.site_name))}</p>'
            f'<h2>{esc(T(lang, "guides"))}</h2><div class="cards">{cards}</div>'
            f'<h2>{esc(T(lang, "reference"))}</h2><div class="cards">{ref}</div>')
    ld = [breadcrumb_ld(s, [(T(lang, "home"), lpath(lang, "/")), (T(lang, "learn_h1"), lpath(lang, "/learn"))])]
    return layout(s, T(lang, "learn_h1"), body, active="learn", path="/learn", lang=lang, ld=ld,
                  **meta(s, "learn", lang))


def article_by_slug(lang: str, slug: str) -> Article | None:
    return next((a for a in ARTICLES_BY_LANG[site_lang(lang)] if a.slug == slug), None)


def learn_article(s: Settings, a: Article, lang: str = "en") -> str:
    lang = site_lang(lang)
    others = "".join(f'<li><a href="/learn/{o.slug}">{esc(o.title)}</a></li>'
                     for o in ARTICLES_BY_LANG[lang] if o.slug != a.slug)
    body = (f'<article class="article"><p class="crumb"><a href="/learn">{esc(T(lang, "learn_h1"))}</a></p>'
            f'<h1>{esc(a.title)}</h1><p class="lead">{esc(a.summary)}</p>{a.body}'
            f'<p class="cta"><a class="button primary" href="/horoscope">{esc(T(lang, "cta_h"))}</a> '
            f'<a class="button" href="/match">{esc(T(lang, "cta_m"))}</a></p>'
            f'<p class="small">{esc(T(lang, "guidance"))}</p>'
            f'<h2>{esc(T(lang, "more_guides"))}</h2><ul>{others}</ul></article>')
    path = f"/learn/{a.slug}"
    desc = a.description or a.summary
    ld = [article_ld(s, lpath(lang, path), a.title, desc, lang),
          breadcrumb_ld(s, [(T(lang, "home"), lpath(lang, "/")), (T(lang, "learn_h1"), lpath(lang, "/learn")),
                            (a.title, lpath(lang, path))])]
    return layout(s, a.title, body, active="learn", path=path, lang=lang, description=desc,
                  page_title=f"{a.seo_title or a.title} | {s.site_name}", ld=ld, og_type="article")
