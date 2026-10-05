# MatchAPI

Indian-astrology marriage matching as a REST API. For a boy and a girl it returns,
independently:

| Method | Key | Result values |
|---|---|---|
| Ashtakoota (36 gunas) | `ashtakoota` | `ADHAMAM` <18 · `MADHYAMAM` 18–24 · `UTTAMAM` 25–32 · `ATI_UTTAMAM` 33–36 |
| Porutham (12, incl. Varna & Nadi) | `porutham` | strict & lenient views: `REJECTED` (Nadi/Vedha fails) · `UTTAMAM` (Rajju, Varna, Nadi, Rasi, Rasyadhipathi, Stree Deergha all match) · `MADHYAMAM` (Rajju matches) · `ADHAMAM` |
| Mangal dosha | `manglik` | per person `NONE/LOW/HIGH/CANCELLED`; pair `NO_DOSHA/MUTUAL/CANCELLED/MISMATCH` |
| KP 7th-cusp sub-lord | `kp7thCusp` | per person `STRONG/PROMISED/MIXED/DENIED`; pair `BOTH_PROMISED/ONE_DENIED/BOTH_DENIED/INCONCLUSIVE` |

There is no combined verdict. Both people's nakshatra, pada, rashi and lagna are always returned.

## Website

The same app serves the free public website **AstroRealm** (server-rendered, nothing is stored; name set by `SITE_NAME`):

* `/horoscope` — birth details (place search or map pin), family and personal details, a rich-text description,
  output language and ayanamsa → a printable **A5** biodata with Rasi/Navamsa charts (KP tables optional).
* `/match` — bride (left) and groom (right) → Ashtakoota and Porutham with both Rasi charts, printable on A5.
  Manglik and KP 7th cusp are hidden on the site until their rules are confirmed (still in the API).
* `/credits`, `/privacy`, `/terms`.

Output languages: English, Tamil, Telugu, Malayalam, Kannada, Hindi. The form itself is in English.
Telugu, Malayalam and Kannada astrology terms (`app/render/i18n.py`, `app/web/strings.py`) are drafts —
please have native speakers review them.

Abuse protection: per-IP rate limit (`RATE_LIMIT_PER_MINUTE`) and Cloudflare Turnstile when its keys are set.
Put the site behind Cloudflare's proxy for DDoS protection. Ad slots (Google AdSense) appear when `ADSENSE_CLIENT`
is set; in development dashed placeholders show where they go. See `.env.example` for every setting.
With `MATCHAPI_ENV=production` the app refuses to start without Turnstile keys and `SOURCE_URL`.

### Licence (AGPL-3.0)

The site uses the Swiss Ephemeris under the AGPL, so the whole project is AGPL-3.0 and the site links to its
source (`SOURCE_URL`). Add the licence text once (the build container can't download it):

```powershell
Invoke-WebRequest https://www.gnu.org/licenses/agpl-3.0.txt -OutFile LICENSE
```

### Deploy on Cloudflare (Containers)

The site runs as a container behind a tiny Worker (`worker/index.js`, `wrangler.jsonc`). Needs the
**Workers Paid plan** ($5/month; includes 25 GiB-hours memory and 375 vCPU-minutes a month), Node.js 20+,
and Docker Desktop running (images are built locally for linux/amd64).

1. Build the place database once: `python scripts/build_geonames.py` → `data/geonames.sqlite` (~150 MB, baked into the image).
2. Add the licence text: `Invoke-WebRequest https://www.gnu.org/licenses/agpl-3.0.txt -OutFile LICENSE`.
3. In `wrangler.jsonc` → `vars`, set `SITE_BASE_URL`, `SOURCE_URL`, `TURNSTILE_SITE_KEY`, `GA_MEASUREMENT_ID`
   (Google Analytics 4, optional) and later the AdSense ids. The app refuses to start in production without the Turnstile keys and `SOURCE_URL`.
4. Deploy:

```powershell
npm install
npx wrangler login
npx wrangler secret put TURNSTILE_SECRET_KEY
npx wrangler deploy
```

5. Add the domain to Cloudflare, then uncomment `routes` in `wrangler.jsonc` and deploy again.
   `npx wrangler tail` shows live logs.

The container uses the `basic` instance (1/4 vCPU, 1 GiB) with one uvicorn worker and sleeps after 10 idle
minutes; the first request after that takes a few seconds while it starts. Cloudflare passes the visitor's
IP in `CF-Connecting-IP`, which the rate limiter uses.

### CI/CD (GitHub Actions)

`.github/workflows/ci.yml` runs the tests on every push and pull request. On a push to `main`, once the
tests pass, it builds the place database (cached for the month) and runs `wrangler deploy`.

One-time setup:

1. Cloudflare dashboard → **My Profile → API Tokens → Create Token** → template **Edit Cloudflare Workers**,
   limited to your account (and the `astrorealm.in` zone). If a deploy fails with a permission error about
   containers or images, edit the token and add the Containers permission.
2. GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**:
   `CLOUDFLARE_API_TOKEN` (the token) and `CLOUDFLARE_ACCOUNT_ID` (Cloudflare dashboard → Workers & Pages,
   right-hand side).
3. Once, from your machine: `npx wrangler secret put TURNSTILE_SECRET_KEY` (secrets stay in Cloudflare across
   deploys; CI never sees them).
4. Optional: GitHub → **Settings → Environments → production** → add yourself as a required reviewer so every
   deploy waits for your approval.

The same Dockerfile runs on any other host too:
`docker build -t astrorealm . ; docker run -p 8000:8000 --env-file .env astrorealm`.

The map uses MapLibre with OpenFreeMap tiles (free, no API key, commercial use allowed; `MAP_STYLE_URL`
switches provider). Before going public: keep `MATCHAPI_NOMINATIM=0`, and get AdSense approval (it needs the privacy page and, for EEA/UK visitors, a
Google-certified consent tool).

## Setup (Windows, Python 3.10+)

```powershell
cd D:\Work\Exploration\MatchMaking\matchapi
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-swisseph.txt   # optional (Swiss Ephemeris)
python scripts\build_geonames.py      # downloads GeoNames (India + world cities500), builds data\geonames.sqlite
python -m uvicorn app.main:app --reload
```

If PowerShell refuses to run `Activate.ps1`, use `.venv\Scripts\python.exe` in place of `python`
(e.g. `.venv\Scripts\python.exe -m uvicorn app.main:app --reload`).

Open http://127.0.0.1:8000/docs for the interactive OpenAPI docs. `GET /health` shows which
ephemeris engine is active and how many places are loaded.

**Swiss Ephemeris on Windows:** `pyswisseph` ships ready-made wheels only for Python 3.6–3.11. On 3.12+ it
needs Microsoft C++ Build Tools to compile. The simplest route is a Python 3.11 venv:

```powershell
winget install -e --id Python.Python.3.11
Remove-Item -Recurse -Force .venv
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-swisseph.txt
```

Without it the API runs on the built-in engine (cusps to ~1″, planets to seconds–minutes of arc).
`GET /health` shows which engine is active.

## Requests

```http
POST /v1/match
{
  "personA": { "sex": "M", "dob": "1990-05-14", "tob": "07:45 PM", "lat": 13.0827, "lon": 80.2707 },
  "personB": { "sex": "F", "dob": "1992-11-02", "tob": "21:10", "place": "Madurai, Tamil Nadu" },
  "options": { "ayanamsa": "LAHIRI", "methods": ["ASHTAKOOTA", "PORUTHAM", "MANGLIK", "KP_7TH_CUSP"] }
}
```

* `tob`: `HH:MM[:SS]` 24-hour, or `hh:mm AM/PM`.
* `name` (optional): echoed in responses and image headings; never used in calculations and never stored.
* Location: either `lat` + `lon`, or `place` (free text; add state/country to disambiguate).
* `utcOffset` (e.g. `"+05:30"`) overrides the time zone **only with `lat`/`lon`**; useful for pre-1956 Indian
  births recorded in local time. With `place` it is ignored (a warning says so). Empty values and the Swagger
  placeholder `"string"` are treated as not supplied.
* `options.ayanamsa`: `LAHIRI` (default) or `KP`. The KP method always uses the KP ayanamsa.
* `options.methods`: any subset; defaults to all four.
* `options.positions` (also on `/v1/chart` and `/v1/chart/image`): `TRUE` (default) = true geometric planet
  positions, as AstroWonder prints them; `APPARENT` = as seen from Earth (light-time and aberration, Swiss
  Ephemeris default). They differ by up to ~40″ (Moon/nodes < 1″), which only ever affects SS/SSS lords.
  Each chart reports `positions` and `positionSensitive` — the planets whose lords would change under the
  other convention.

Other endpoints: `POST /v1/chart` (single person), `GET /v1/places?q=Salem` (place candidates) and
`POST /v1/chart/image` — an SVG with the South Indian Rasi and Navamsa charts plus KP planet/cusp tables:

```json
{ "person": { "name": "Meena", "sex": "F", "dob": "2012-04-18", "tob": "09:25", "place": "Chennai" },
  "ayanamsa": "KP", "lang": "ta", "include": ["RASI", "NAVAMSA", "KP_TABLES"] }
```

`lang` is `en`, `ta` or `hi`; add a language in `app/render/i18n.py`. Open the SVG in a browser or embed it
with `<img>`. Retrograde planets are marked (R)/(வ)/(व).

Errors are `422` with `{"error": CODE, "message": ...}`; codes include `INVALID_TIME`, `INVALID_DATE`,
`AMBIGUOUS_PLACE` (with `candidates`), `PLACE_NOT_FOUND`, `TIMEZONE_UNRESOLVED`. `GEO_DATA_MISSING` is `503`.

## How it works

1. **Place** → local GeoNames SQLite (fuzzy match, state/country hints, India preferred when no country is
   given) → OpenStreetMap Nominatim fallback (cached). Coordinates → time zone via `timezonefinder`,
   else the nearest GeoNames place.
2. **Time** → IANA tz rules (incl. India's 1942–45 +06:30) → UTC → Julian Day.
3. **Ephemeris** → Swiss Ephemeris if installed, else the built-in engine (Meeus Moon/Sun, JPL Kepler
   elements for planets, Placidus by iteration). Force one with `MATCHAPI_ENGINE=builtin|swisseph`.
4. **Chart** → sidereal positions, nakshatra/pada/rashi, KP star- and sub-lords, Placidus houses.
5. **Matchers** → `app/matching/*`, all tables and thresholds in `app/rules/v1.py`.

Warnings are returned when the Moon is near a nakshatra boundary, the lagna is near a sign
boundary, or the KP 7th-cusp sub-lord changes within ±5 minutes of the birth time.

## Rules to confirm with the astrologer

Marked `VERIFY` in `app/rules/v1.py`: the Vashya score table, Dina partial for same nakshatra,
Stree Deergha partial range (8–13), Rasi porutham counts (1, 7, 9, 10, 11 match; 12 partial).
Also worth confirming: Mangal dosha houses (1, 2, 4, 7, 8, 12) and cancellations, and KP node handling
(nodes take their sign lord's houses).

## Tests

```powershell
pytest
```

* `tests/fixtures/private/golden_charts.json` (git-ignored: real people's birth data, never pushed) — add the astrologer's verified charts here; `test_golden.py` checks
  nakshatra, pada, rashi, lagna and KP 7th sub-lord against them.
* `tests/fixtures/private/golden_matches.json` (git-ignored) — pair results the astrologer validated; `test_golden_matches.py` runs
  `/v1/match` logic on them, asserting only the methods listed in each case's `verified`. Ashtakoota/Porutham
  are checked on every engine; lagna, Manglik and KP 7th cusp only on Swiss Ephemeris (they are
  time-sensitive). Add new pairs without names.
* With `pyswisseph` installed, `test_golden.py` also cross-checks the built-in engine against Swiss Ephemeris.

## Configuration (environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `MATCHAPI_ENGINE` | `auto` | `auto`, `swisseph`, `builtin` |
| `MATCHAPI_POSITIONS` | `TRUE` | Server default for `options.positions`: `TRUE` (matches AstroWonder) or `APPARENT` |
| `SE_EPHE_PATH` | – | Folder with Swiss `.se1` files (otherwise Moshier, ~1″) |
| `MATCHAPI_GEO_DB` | `data/geonames.sqlite` | Place database path |
| `MATCHAPI_DEFAULT_COUNTRY` | `IN` | Preferred country when the place has no country hint |
| `MATCHAPI_NOMINATIM` | `1` | Set `0` to disable the online fallback |

## Licences

* Swiss Ephemeris / pyswisseph: AGPL (or Astrodienst commercial licence).
* Place data © GeoNames (geonames.org), CC BY 4.0. Fallback geocoding © OpenStreetMap contributors (ODbL).
