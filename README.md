# MatchAPI

Indian-astrology marriage matching as a REST API. For a boy and a girl it returns,
independently:

| Method | Key | Result values |
|---|---|---|
| Ashtakoota (36 gunas) | `ashtakoota` | `ADHAMAM` <18 · `MADHYAMAM` 18–24 · `UTTAMAM` 25–32 · `ATI_UTTAMAM` 33–36 |
| Porutham (12, incl. Varna & Nadi) | `porutham` | strict & lenient views: `REJECTED` (Nadi/Vedha fails) · `UTTAMAM` (Rajju, Varna, Nadi, Rasi, Rasyadhipathi, Stree Deergha all match) · `MADHYAMAM` (Rajju matches) · `ADHAMAM` |
| Mangal (Chevvai/Manglik) dosha | `manglik` | two rule sets, `details.south` and `details.north` (top-level `result` = South). Per person `NONE/MILD/STRONG/CANCELLED` with the factors that raised, lowered, reduced or cancelled it; pair `NO_DOSHA/CANCELLED/MUTUAL/PARTLY_BALANCED/ONE_SIDED` |
| Rahu/Ketu in the 7th (advisory) | `rahuKetu` | per person `NONE/MILD/STRONG` + Kala Sarpa note; pair `NO_DOSHA/SHARED/ONE_SIDED` |
| KP 7th-cusp sub-lord | `kp7thCusp` | per person `STRONG/PROMISED/MIXED/DENIED`; pair `BOTH_PROMISED/ONE_DENIED/BOTH_DENIED/INCONCLUSIVE` |

There is no combined verdict. Both people's nakshatra, pada, rashi and lagna are always returned.

## Website

The same app serves the free public website **AstroRealm** (server-rendered, nothing is stored; name set by `SITE_NAME`):

* `/horoscope` — birth details (place search or map pin), family and personal details, a rich-text description,
  output language and ayanamsa → a printable **A5** biodata with Rasi/Navamsa charts (KP tables optional).
* `/match` — bride (left) and groom (right) → Ashtakoota and Porutham with both Rasi charts, then a doshas page:
  Chevvai/Manglik under both the South and North Indian rules, and Rahu/Ketu in the 7th. Printable on A5.
  KP 7th cusp is hidden on the site until its rules are confirmed (still in the API).
* `/credits`, `/privacy`, `/terms`.

Output languages: English, Tamil, Telugu, Malayalam, Kannada, Hindi. The form itself is in English.
Telugu, Malayalam and Kannada astrology terms (`app/render/i18n.py`, `app/web/strings.py`) are drafts —
please have native speakers review them.

Abuse protection: per-IP rate limit (`RATE_LIMIT_PER_MINUTE`) and Cloudflare Turnstile when its keys are set. Ad slots (Google AdSense) appear when `ADSENSE_CLIENT`
is set; in development dashed placeholders show where they go. See `.env.example` for every setting.
With `MATCHAPI_ENV=production` the app refuses to start without Turnstile keys and `SOURCE_URL`.

### Licence (AGPL-3.0)

The site uses the Swiss Ephemeris under the AGPL, so the whole project is AGPL-3.0 and the site links to its
source (`SOURCE_URL`). Add the licence text once (the build container can't download it):

```powershell
Invoke-WebRequest https://www.gnu.org/licenses/agpl-3.0.txt -OutFile LICENSE
```

### Deploy on Google Cloud (Cloud Run + Firebase Hosting)

The app runs as a container on **Cloud Run** in Mumbai (`asia-south1`). **Firebase Hosting** puts it on
`astrorealm.in` with a free SSL certificate while the domain's DNS stays at GoDaddy (Cloud Run's own domain
mapping isn't offered in Mumbai). At low traffic this stays within Google's free tiers; the project needs a
billing account (Firebase's Blaze plan) — set a budget alert.

Files: `Dockerfile`, `deploy/cloudrun.env.yaml` (non-secret settings), `firebase.json` and `.firebaserc`
(Hosting rewrite to the Cloud Run service), `deploy/ar-cleanup-policy.json` (keeps only recent images).

**One-time setup** (Google Cloud Shell or the `gcloud` CLI; replace the project id). Run it from the
repository root — in Cloud Shell, clone it first:

```bash
git clone https://github.com/vivek-dhayalan/astrorealm-website.git && cd astrorealm-website
PROJECT=astrorealm-510714           # your project id (also put it in .firebaserc)
REPO=vivek-dhayalan/astrorealm-website
gcloud config set project $PROJECT
NUMBER=$(gcloud projects describe $PROJECT --format='value(projectNumber)')
gcloud services enable run.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com \
  iamcredentials.googleapis.com sts.googleapis.com firebase.googleapis.com firebasehosting.googleapis.com \
  cloudresourcemanager.googleapis.com
firebase login --no-localhost                    # Cloud Shell's own credentials can't add Firebase
firebase projects:addfirebase $PROJECT

# image registry in Mumbai, keeping only the newest images
gcloud artifacts repositories create astrorealm --repository-format=docker --location=asia-south1
gcloud artifacts repositories set-cleanup-policies astrorealm --location=asia-south1 \
  --policy=deploy/ar-cleanup-policy.json --no-dry-run

# Turnstile secret (paste the secret key when prompted, then Ctrl-D)
gcloud secrets create turnstile-secret --data-file=-
gcloud secrets add-iam-policy-binding turnstile-secret \
  --member=serviceAccount:$NUMBER-compute@developer.gserviceaccount.com --role=roles/secretmanager.secretAccessor

# deploy identity for GitHub Actions
gcloud iam service-accounts create github-deploy --display-name="GitHub deploy"
SA=github-deploy@$PROJECT.iam.gserviceaccount.com
for ROLE in roles/run.admin roles/artifactregistry.writer roles/firebasehosting.admin; do
  gcloud projects add-iam-policy-binding $PROJECT --member=serviceAccount:$SA --role=$ROLE
done
gcloud iam service-accounts add-iam-policy-binding $NUMBER-compute@developer.gserviceaccount.com \
  --member=serviceAccount:$SA --role=roles/iam.serviceAccountUser

# let only this GitHub repo act as that identity (no keys stored anywhere)
gcloud iam workload-identity-pools create github --location=global --display-name="GitHub"
gcloud iam workload-identity-pools providers create-oidc github --location=global --workload-identity-pool=github \
  --issuer-uri=https://token.actions.githubusercontent.com \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='$REPO'"
gcloud iam service-accounts add-iam-policy-binding $SA --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/$NUMBER/locations/global/workloadIdentityPools/github/attribute.repository/$REPO"
echo "GCP_WIF_PROVIDER = projects/$NUMBER/locations/global/workloadIdentityPools/github/providers/github"
echo "GCP_DEPLOY_SA    = $SA"
```

Then:

1. **GitHub** → Settings → Secrets and variables → Actions: variable `GCP_PROJECT_ID`; secrets `GCP_WIF_PROVIDER`
   and `GCP_DEPLOY_SA` (the two values printed above).
2. Fill in `TURNSTILE_SITE_KEY` (and later `GA_MEASUREMENT_ID`) in `deploy/cloudrun.env.yaml`.
3. Push to `main`: CI tests, builds the image, deploys Cloud Run and publishes Firebase Hosting.
4. **Firebase console** → add Firebase to the same Google Cloud project → Hosting → **Add custom domain**
   `astrorealm.in` (and `www.astrorealm.in`, redirecting to it). Firebase shows a TXT record and A record(s).
5. **GoDaddy** → My Products → astrorealm.in → DNS: delete GoDaddy's default "Parked" A record and any
   forwarding, then add the records Firebase showed. SSL is issued automatically (minutes to a few hours).
6. **Billing** → Budgets & alerts: add a small monthly budget (e.g. ₹500) with email alerts.
7. In Cloudflare Turnstile, set the widget's hostname to `astrorealm.in` (Turnstile still works; only hosting moved).

Notes: Cloud Run scales to zero, so the first visit after a quiet spell takes a few seconds. Firebase Hosting
forwards no cookies except `__session` — the site uses none. The visitor IP for rate limiting comes from
`X-Forwarded-For` (`CLIENT_IP_HEADER`); it can be forged, so Turnstile remains the real bot check.

The same Dockerfile runs anywhere: `docker build -t astrorealm . ; docker run -p 8080:8080 --env-file .env astrorealm`.

### CI/CD (GitHub Actions)

`.github/workflows/ci.yml` runs the tests on every push and pull request. On a push to `main`, once the tests
pass, it builds the place database (cached for the month), builds and pushes the image to Artifact Registry,
deploys Cloud Run and publishes Firebase Hosting. GitHub signs in to Google with Workload Identity Federation,
so no Google key is stored in GitHub. Optional: GitHub → Settings → Environments → `production` → add yourself
as a required reviewer so each deploy waits for your approval.

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
  "personA": { "sex": "M", "dob": "1991-09-23", "tob": "06:30 AM", "lat": 13.0827, "lon": 80.2707 },
  "personB": { "sex": "F", "dob": "1992-11-02", "tob": "21:10", "place": "Madurai, Tamil Nadu" },
  "options": { "ayanamsa": "LAHIRI", "methods": ["ASHTAKOOTA", "PORUTHAM", "MANGLIK", "RAHU_KETU", "KP_7TH_CUSP"] }
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

Other endpoints: `POST /v1/chart` (single person, including its Vimshottari `dasha`: balance at birth, current
mahadasha/bhukti/antara with time left, and the mahadasha and current bhukti tables), `POST /v1/naming` (baby naming:
the Moon's nakshatra pada with its starting syllables in every script — variants included — the pada's start and end
times, birth/destiny/harmony numbers, and Chaldean, Pythagorean and pyramid numbers for any `names` given),
`GET /v1/places?q=Salem` (place candidates) and
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
Also worth confirming: the Mangal dosha rule sets (`MANGLIK_TRADITIONS`: houses, reference points, cancellations,
house weights), the Rahu/Ketu grading (`NODE_*`), and KP node handling
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
