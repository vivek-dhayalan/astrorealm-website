"""Server-rendered website: horoscope and matching pages (generate only — nothing is stored)."""
from __future__ import annotations

import time

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

from ..core.ayanamsa import Ayanamsa
from ..core import dasha as dasha_engine
from ..core.timeutil import InputError
from ..geo import get_resolver
from ..matching import ashtakoota, kp, manglik, nodes, porutham
from ..matching.manglik import TRADITIONS
from ..render import svg
from ..service import ResolvedPerson
from . import refpages, stars, views
from .learn import ARTICLES
from .forms import DashaForm, HoroscopeForm, MatchForm, parse_body
from .security import RateLimiter, client_ip, verify_turnstile
from .settings import get_settings
from .strings import LANGS
from .ui import SITE_LANGS, lpath, prefix

router = APIRouter(include_in_schema=False)
_limiter: RateLimiter | None = None

NO_STORE = {"Cache-Control": "no-store", "X-Robots-Tag": "noindex", "Referrer-Policy": "same-origin"}
PAGE = {"Referrer-Policy": "same-origin", "X-Content-Type-Options": "nosniff", "Cache-Control": "no-cache"}


def limiter() -> RateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter(get_settings().rate_per_minute)
    return _limiter


def html(content: str, status: int = 200, private: bool = False) -> HTMLResponse:
    return HTMLResponse(content, status_code=status, headers=NO_STORE if private else PAGE)


async def _guard(request: Request, form: dict) -> str | None:
    """Rate limit and bot check. Returns an error message, or None when the request may proceed."""
    s = get_settings()
    ip = client_ip(request.headers, request.client.host if request.client else None, get_settings().client_ip_header)
    if not limiter().allow(ip):
        return "Too many requests from your network. Please wait a minute and try again."
    if s.turnstile_enabled:
        token = (form.get("cf-turnstile-response") or [""])[0]
        if not await verify_turnstile(s.turnstile_secret, token, ip):
            return "The bot check didn't pass. Please wait for it to finish, then submit again."
    return None


def _place_label(b, rp: ResolvedPerson) -> str:
    if rp.place:
        return ", ".join(x for x in (rp.place.get("name"), rp.place.get("admin1"), rp.place.get("countryName")) if x)
    if b.place:
        return b.place
    return f"{rp.lat:.4f}, {rp.lon:.4f}"


def _input_error_message(exc: InputError) -> tuple[str, list | None]:
    if exc.code == "AMBIGUOUS_PLACE":
        return "Several places match that name.", exc.extra.get("candidates")
    if exc.code == "PLACE_NOT_FOUND":
        return "We couldn't find that place. Check the spelling, add the state, or pick it on the map.", None
    if exc.code == "TIMEZONE_UNRESOLVED":
        return "We couldn't work out the time zone for that location. Please choose a nearby town instead.", None
    return exc.message, None


# ------------------------------------------------------------------ pages
# Every public page exists in each site language: /x (English), /ta/x (Tamil), /hi/x (Hindi).
def _localized(path: str, handler, with_slug: bool = False) -> None:
    for code in SITE_LANGS:
        url = lpath(code, path) if "{" not in path else prefix(code) + path

        def make(lang):
            if with_slug:
                def endpoint(slug: str):
                    return handler(lang, slug)
            else:
                def endpoint(request: Request):
                    return handler(lang, request)
            return endpoint
        router.add_api_route(url, make(code), methods=["GET"], response_class=HTMLResponse, include_in_schema=False)


def _ui(form: dict) -> str:
    """Site language the form was sent from (hidden field), so the result page keeps it."""
    v = (form.get("ui") or [""])[0]
    return v if v in SITE_LANGS else "en"


def _output_lang(lang: str, request: Request) -> str:
    """Output language preselected on the forms: ?lang= if given, else the site language."""
    q = request.query_params.get("lang", "")
    return q if q in LANGS else lang


def _not_found(lang: str):
    return html(views.not_found(get_settings(), lang), 404)


_localized("/", lambda lang, r: html(views.home(get_settings(), lang)))
_localized("/horoscope", lambda lang, r: html(views.horoscope_form(
    get_settings(), HoroscopeForm(lang=_output_lang(lang, r)), ui=lang)))
_localized("/dasha", lambda lang, r: html(views.dasha_form(get_settings(), DashaForm(), ui=lang)))
_localized("/match", lambda lang, r: html(views.match_form(
    get_settings(), MatchForm(lang=_output_lang(lang, r)), ui=lang)))
_localized("/credits", lambda lang, r: html(views.credits(get_settings(), lang)))
_localized("/privacy", lambda lang, r: html(views.privacy(get_settings(), lang)))
_localized("/terms", lambda lang, r: html(views.terms(get_settings(), lang)))
_localized("/upcoming", lambda lang, r: html(views.upcoming(get_settings(), lang)))
_localized("/learn", lambda lang, r: html(views.learn_index(get_settings(), lang)))
_localized("/learn/nakshatras", lambda lang, r: html(refpages.nakshatra_index(get_settings(), lang)))
_localized("/learn/rasis", lambda lang, r: html(refpages.rasi_index(get_settings(), lang)))
_localized(refpages.TABLE_PATH, lambda lang, r: html(refpages.porutham_table(get_settings(), lang)))


def _nakshatra(lang: str, slug: str):
    n = stars.NAK_BY_SLUG.get(slug)
    return _not_found(lang) if n is None else html(refpages.nakshatra_page(get_settings(), n, lang))


def _rasi(lang: str, slug: str):
    r = stars.RASI_BY_SLUG.get(slug)
    return _not_found(lang) if r is None else html(refpages.rasi_page(get_settings(), r, lang))


def _article(lang: str, slug: str):
    a = views.article_by_slug(lang, slug)
    return _not_found(lang) if a is None else html(views.learn_article(get_settings(), a, lang))


@router.get("/hi/learn/guna-milan")
def old_guna_milan():
    """Earlier address of the Hindi Ashtakoota article."""
    return RedirectResponse("/hi/learn/ashtakoota", status_code=301)


_localized("/learn/nakshatra/{slug}", _nakshatra, with_slug=True)
_localized("/learn/rasi/{slug}", _rasi, with_slug=True)
_localized("/learn/{slug}", _article, with_slug=True)


@router.post("/horoscope", response_class=HTMLResponse)
async def horoscope_submit(request: Request):
    s = get_settings()
    try:
        form = parse_body(await request.body())
    except ValueError as exc:
        return html(views.error_page(s, "Form too large", str(exc)), 413, private=True)
    ui = _ui(form)
    frm = HoroscopeForm.parse(form)
    blocked = await _guard(request, form)
    if blocked:
        return html(views.horoscope_form(s, frm, blocked, ui=ui), 429 if "Too many" in blocked else 400, private=True)
    if frm.errors:
        return html(views.horoscope_form(s, frm, "Please check the highlighted fields.", ui=ui), 422, private=True)
    try:
        rp = ResolvedPerson(frm.birth.to_person())
        chart = rp.chart(frm.ayanamsa)
        kc = rp.chart(Ayanamsa.KP) if "KP_TABLES" in frm.parts else None
        by_lang = {}
        for lg in frm.langs:
            svgs = {part: svg.grid_svg(chart, lg, part, degrees=False)
                    for part in ("RASI", "NAVAMSA") if part in frm.parts}
            if kc is not None:
                svgs["KP_TABLES"] = svg.kp_svg(kc, kp.planet_significations(kc), lg, compact=True)
            by_lang[lg] = svgs
        dasha = rp.dasha(frm.ayanamsa) if "DASHA" in frm.parts else None
        doshas = None
        if "DOSHAS" in frm.parts:
            doshas = {"manglik": {t.lower(): manglik.assess(chart, t) for t in TRADITIONS},
                      "rahuKetu": nodes.assess(chart)}
    except InputError as exc:
        msg, cands = _input_error_message(exc)
        frm.errors["place" if "PLACE" in exc.code else "dob"] = msg
        return html(views.horoscope_form(s, frm, msg, cands, ui=ui), 422, private=True)
    return html(views.horoscope_result(s, frm, _place_label(frm.birth, rp), chart, by_lang[frm.lang], ui=ui,
                                       doshas=doshas, svgs_by_lang=by_lang, dasha=dasha), private=True)


@router.post("/dasha", response_class=HTMLResponse)
async def dasha_submit(request: Request):
    s = get_settings()
    try:
        form = parse_body(await request.body())
    except ValueError as exc:
        return html(views.error_page(s, "Form too large", str(exc)), 413, private=True)
    ui = _ui(form)
    frm = DashaForm.parse(form)
    blocked = await _guard(request, form)
    if blocked:
        return html(views.dasha_form(s, frm, blocked, ui=ui), 429 if "Too many" in blocked else 400, private=True)
    if frm.errors:
        return html(views.dasha_form(s, frm, "Please check the highlighted fields.", ui=ui), 422, private=True)
    try:
        rp = ResolvedPerson(frm.birth.to_person())
        chart = rp.chart(frm.ayanamsa)
    except InputError as exc:
        msg, cands = _input_error_message(exc)
        frm.errors["place" if "PLACE" in exc.code else "dob"] = msg
        return html(views.dasha_form(s, frm, msg, cands, ui=ui), 422, private=True)
    d = rp.dasha(frm.ayanamsa)
    mds, _ = dasha_engine.mahadashas(chart.moon.longitude, rp.time.utc)
    offset_min = round((rp.time.local - rp.time.utc.replace(tzinfo=None)).total_seconds() / 60)
    return html(views.dasha_result(s, frm, _place_label(frm.birth, rp), chart, d, mds,
                                   int(rp.time.utc.timestamp() * 1000), offset_min, int(time.time() * 1000), ui=ui),
                private=True)


@router.post("/match", response_class=HTMLResponse)
async def match_submit(request: Request):
    s = get_settings()
    try:
        form = parse_body(await request.body())
    except ValueError as exc:
        return html(views.error_page(s, "Form too large", str(exc)), 413, private=True)
    ui = _ui(form)
    frm = MatchForm.parse(form)
    blocked = await _guard(request, form)
    if blocked:
        return html(views.match_form(s, frm, blocked, ui=ui), 429 if "Too many" in blocked else 400, private=True)
    if frm.errors:
        return html(views.match_form(s, frm, "Please check the highlighted fields.", ui=ui), 422, private=True)
    people = {}
    for role, b, prefix_ in (("bride", frm.bride, "b_"), ("groom", frm.groom, "g_")):
        try:
            people[role] = ResolvedPerson(b.to_person())
        except InputError as exc:
            msg, cands = _input_error_message(exc)
            frm.errors[prefix_ + "place"] = msg
            return html(views.match_form(s, frm, f"{role.title()}: {msg}", cands, ui=ui), 422, private=True)
    charts = {r: p.chart(frm.ayanamsa) for r, p in people.items()}
    by_lang = {lg: {r: svg.grid_svg(c, lg, "RASI", degrees=False) for r, c in charts.items()} for lg in frm.langs}
    svgs = by_lang[frm.lang]
    labels = {"bride": _place_label(frm.bride, people["bride"]), "groom": _place_label(frm.groom, people["groom"])}
    # matchers take (boy, girl)
    ashta = ashtakoota.match(charts["groom"], charts["bride"])
    poru = porutham.match(charts["groom"], charts["bride"])
    mang = manglik.match(charts["groom"], charts["bride"])
    rahu = nodes.match(charts["groom"], charts["bride"])
    dashas = {r: p.dasha(frm.ayanamsa) for r, p in people.items()}
    return html(views.match_result(s, frm, labels, charts, svgs, ashta, poru, ui=ui, mang=mang, rahu=rahu,
                                   svgs_by_lang=by_lang, dashas=dashas), private=True)


def site_paths() -> list[str]:
    """Language-neutral paths of every public page (the sitemap lists each in every language)."""
    return (["/", "/horoscope", "/match", "/dasha", "/learn"] + [f"/learn/{a.slug}" for a in ARTICLES]
            + refpages.sitemap_paths() + ["/upcoming", "/credits", "/privacy", "/terms"])


@router.get("/sitemap.xml")
def sitemap():
    base = (get_settings().base_url or "").rstrip("/")
    urls = "".join(f"<url><loc>{base}{lpath(code, p)}</loc></url>" for p in site_paths() for code in SITE_LANGS)
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
    return Response(xml, media_type="application/xml")


@router.get("/ads.txt", response_class=HTMLResponse)
def ads_txt():
    """Authorised ad sellers file, required by AdSense once ADSENSE_CLIENT is set."""
    client = get_settings().adsense_client
    if not client:
        return HTMLResponse("", status_code=404, media_type="text/plain")
    pub = client.removeprefix("ca-")
    return HTMLResponse(f"google.com, {pub}, DIRECT, f08c47fec0942fa0\n", media_type="text/plain")


@router.get("/robots.txt", response_class=HTMLResponse)
def robots():
    base = (get_settings().base_url or "").rstrip("/")
    sm = f"Sitemap: {base}/sitemap.xml\n" if base else ""
    return HTMLResponse("User-agent: *\nDisallow: /v1/\nAllow: /\n" + sm, media_type="text/plain")


# ------------------------------------------------------------------ helpers for the place widget
@router.get("/v1/places/nearest")
def nearest_place(request: Request, lat: float = Query(..., ge=-90, le=90), lon: float = Query(..., ge=-180, le=180)):
    ip = client_ip(request.headers, request.client.host if request.client else None, get_settings().client_ip_header)
    if not limiter().allow("near:" + ip):
        return JSONResponse({"error": "RATE_LIMITED"}, status_code=429)
    r = get_resolver()
    place = r.store.nearest(lat, lon) if r.store else None
    return {"lat": lat, "lon": lon, "nearest": place.to_dict() if place else None}
