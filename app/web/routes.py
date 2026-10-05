"""Server-rendered website: horoscope and matching pages (generate only — nothing is stored)."""
from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from ..core.ayanamsa import Ayanamsa
from ..core.timeutil import InputError
from ..geo import get_resolver
from ..matching import ashtakoota, kp, porutham
from ..render import svg
from ..service import ResolvedPerson
from . import views
from .learn import ARTICLES, BY_SLUG
from .forms import HoroscopeForm, MatchForm, parse_body
from .security import RateLimiter, client_ip, verify_turnstile
from .settings import get_settings

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
@router.get("/", response_class=HTMLResponse)
def home():
    return html(views.home(get_settings()))


@router.get("/horoscope", response_class=HTMLResponse)
def horoscope_page():
    return html(views.horoscope_form(get_settings(), HoroscopeForm()))


@router.post("/horoscope", response_class=HTMLResponse)
async def horoscope_submit(request: Request):
    s = get_settings()
    try:
        form = parse_body(await request.body())
    except ValueError as exc:
        return html(views.error_page(s, "Form too large", str(exc)), 413, private=True)
    frm = HoroscopeForm.parse(form)
    blocked = await _guard(request, form)
    if blocked:
        return html(views.horoscope_form(s, frm, blocked), 429 if "Too many" in blocked else 400, private=True)
    if frm.errors:
        return html(views.horoscope_form(s, frm, "Please check the highlighted fields."), 422, private=True)
    try:
        rp = ResolvedPerson(frm.birth.to_person())
        chart = rp.chart(frm.ayanamsa)
        svgs = {}
        for part in ("RASI", "NAVAMSA"):
            if part in frm.parts:
                svgs[part] = svg.grid_svg(chart, frm.lang, part, degrees=False)
        if "KP_TABLES" in frm.parts:
            kc = rp.chart(Ayanamsa.KP)
            svgs["KP_TABLES"] = svg.kp_svg(kc, kp.planet_significations(kc), frm.lang, compact=True)
    except InputError as exc:
        msg, cands = _input_error_message(exc)
        frm.errors["place" if "PLACE" in exc.code else "dob"] = msg
        return html(views.horoscope_form(s, frm, msg, cands), 422, private=True)
    return html(views.horoscope_result(s, frm, _place_label(frm.birth, rp), chart, svgs), private=True)


@router.get("/match", response_class=HTMLResponse)
def match_page():
    return html(views.match_form(get_settings(), MatchForm()))


@router.post("/match", response_class=HTMLResponse)
async def match_submit(request: Request):
    s = get_settings()
    try:
        form = parse_body(await request.body())
    except ValueError as exc:
        return html(views.error_page(s, "Form too large", str(exc)), 413, private=True)
    frm = MatchForm.parse(form)
    blocked = await _guard(request, form)
    if blocked:
        return html(views.match_form(s, frm, blocked), 429 if "Too many" in blocked else 400, private=True)
    if frm.errors:
        return html(views.match_form(s, frm, "Please check the highlighted fields."), 422, private=True)
    people = {}
    for role, b, prefix in (("bride", frm.bride, "b_"), ("groom", frm.groom, "g_")):
        try:
            people[role] = ResolvedPerson(b.to_person())
        except InputError as exc:
            msg, cands = _input_error_message(exc)
            frm.errors[prefix + "place"] = msg
            return html(views.match_form(s, frm, f"{role.title()}: {msg}", cands), 422, private=True)
    charts = {r: p.chart(frm.ayanamsa) for r, p in people.items()}
    svgs = {r: svg.grid_svg(c, frm.lang, "RASI", degrees=False) for r, c in charts.items()}
    labels = {"bride": _place_label(frm.bride, people["bride"]), "groom": _place_label(frm.groom, people["groom"])}
    # matchers take (boy, girl)
    ashta = ashtakoota.match(charts["groom"], charts["bride"])
    poru = porutham.match(charts["groom"], charts["bride"])
    return html(views.match_result(s, frm, labels, charts, svgs, ashta, poru), private=True)


@router.get("/credits", response_class=HTMLResponse)
def credits_page():
    return html(views.credits(get_settings()))


@router.get("/privacy", response_class=HTMLResponse)
def privacy_page():
    return html(views.privacy(get_settings()))


@router.get("/terms", response_class=HTMLResponse)
def terms_page():
    return html(views.terms(get_settings()))


@router.get("/upcoming", response_class=HTMLResponse)
def upcoming_page():
    return html(views.upcoming(get_settings()))


@router.get("/learn", response_class=HTMLResponse)
def learn_index():
    return html(views.learn_index(get_settings()))


@router.get("/learn/{slug}", response_class=HTMLResponse)
def learn_article(slug: str):
    article = BY_SLUG.get(slug)
    if article is None:
        return html(views.error_page(get_settings(), "Not found", "That guide doesn't exist."), 404)
    return html(views.learn_article(get_settings(), article))


@router.get("/sitemap.xml")
def sitemap():
    base = (get_settings().base_url or "").rstrip("/")
    paths = ["/", "/horoscope", "/match", "/learn"] + [f"/learn/{a.slug}" for a in ARTICLES] + \
            ["/upcoming", "/credits", "/privacy", "/terms"]
    urls = "".join(f"<url><loc>{base}{p}</loc></url>" for p in paths)
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
