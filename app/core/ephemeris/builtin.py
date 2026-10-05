"""Pure-Python ephemeris (no external dependencies).

* Moon  — Meeus, Astronomical Algorithms ch. 47 (ELP-2000/82 truncated, ~10")
* Sun   — Meeus ch. 25 (~0.01°)
* Planets — JPL Keplerian elements (Standish, valid 1800–2050; ~1' inner, few ' outer)
* Houses — Placidus by iteration; Ascendant/MC closed form

Accurate enough for nakshatra/pada and sign-level work and for cross-checking.
Swiss Ephemeris is preferred when installed.
"""
from __future__ import annotations

import math

from ..ayanamsa import Ayanamsa, ayanamsa_deg, general_precession_arcsec
from ..reference import norm360
from ..timeutil import delta_t_seconds
from .base import DEFAULT_POSITION_MODE, EphemerisEngine, HouseResult, PositionMode

D2R = math.pi / 180.0
R2D = 180.0 / math.pi


def _sin(x):
    return math.sin(x * D2R)


def _cos(x):
    return math.cos(x * D2R)


# --------------------------------------------------------------------------- Moon
# (D, M, M', F, coefficient of sin for longitude ×1e-6 deg)
_MOON_LON = [
    (0, 0, 1, 0, 6288774), (2, 0, -1, 0, 1274027), (2, 0, 0, 0, 658314), (0, 0, 2, 0, 213618),
    (0, 1, 0, 0, -185116), (0, 0, 0, 2, -114332), (2, 0, -2, 0, 58793), (2, -1, -1, 0, 57066),
    (2, 0, 1, 0, 53322), (2, -1, 0, 0, 45758), (0, 1, -1, 0, -40923), (1, 0, 0, 0, -34720),
    (0, 1, 1, 0, -30383), (2, 0, 0, -2, 15327), (0, 0, 1, 2, -12528), (0, 0, 1, -2, 10980),
    (4, 0, -1, 0, 10675), (0, 0, 3, 0, 10034), (4, 0, -2, 0, 8548), (2, 1, -1, 0, -7888),
    (2, 1, 0, 0, -6766), (1, 0, -1, 0, -5163), (1, 1, 0, 0, 4987), (2, -1, 1, 0, 4036),
    (2, 0, 2, 0, 3994), (4, 0, 0, 0, 3861), (2, 0, -3, 0, 3665), (0, 1, -2, 0, -2689),
    (2, 0, -1, 2, -2602), (2, -1, -2, 0, 2390), (1, 0, 1, 0, -2348), (2, -2, 0, 0, 2236),
    (0, 1, 2, 0, -2120), (0, 2, 0, 0, -2069), (2, -2, -1, 0, 2048), (2, 0, 1, -2, -1773),
    (2, 0, 0, 2, -1595), (4, -1, -1, 0, 1215), (0, 0, 2, 2, -1110), (3, 0, -1, 0, -892),
    (2, 1, 1, 0, -810), (4, -1, -2, 0, 759), (0, 2, -1, 0, -713), (2, 2, -1, 0, -700),
    (2, 1, -2, 0, 691), (2, -1, 0, -2, 596), (4, 0, 1, 0, 549), (0, 0, 4, 0, 537),
    (4, -1, 0, 0, 520), (1, 0, -2, 0, -487), (2, 1, 0, -2, -399), (0, 0, 2, -2, -381),
    (1, 1, 1, 0, 351), (3, 0, -2, 0, -340), (4, 0, -3, 0, 330), (2, -1, 2, 0, 327),
    (0, 2, 1, 0, -323), (1, 1, -1, 0, 299), (2, 0, 3, 0, 294),
]


def moon_longitude_tropical(jd_tt: float) -> float:
    """Geocentric ecliptic longitude of the Moon, mean equinox of date (no nutation)."""
    t = (jd_tt - 2451545.0) / 36525.0
    lp = 218.3164477 + 481267.88123421 * t - 0.0015786 * t**2 + t**3 / 538841 - t**4 / 65194000
    d = 297.8501921 + 445267.1114034 * t - 0.0018819 * t**2 + t**3 / 545868 - t**4 / 113065000
    m = 357.5291092 + 35999.0502909 * t - 0.0001536 * t**2 + t**3 / 24490000
    mp = 134.9633964 + 477198.8675055 * t + 0.0087414 * t**2 + t**3 / 69699 - t**4 / 14712000
    f = 93.2720950 + 483202.0175233 * t - 0.0036539 * t**2 - t**3 / 3526000 + t**4 / 863310000
    a1 = 119.75 + 131.849 * t
    a2 = 53.09 + 479264.290 * t
    e = 1 - 0.002516 * t - 0.0000074 * t**2
    sl = 0.0
    for cd, cm, cmp_, cf, coef in _MOON_LON:
        term = coef * _sin(cd * d + cm * m + cmp_ * mp + cf * f)
        if abs(cm) == 1:
            term *= e
        elif abs(cm) == 2:
            term *= e * e
        sl += term
    sl += 3958 * _sin(a1) + 1962 * _sin(lp - f) + 318 * _sin(a2)
    return norm360(lp + sl / 1e6)


def mean_node_tropical(jd_tt: float) -> float:
    t = (jd_tt - 2451545.0) / 36525.0
    return norm360(125.0445479 - 1934.1362891 * t + 0.0020754 * t**2 + t**3 / 467441 - t**4 / 60616000)


# ---------------------------------------------------------------------------- Sun
def sun_longitude_tropical(jd_tt: float, apparent: bool = False) -> float:
    """Apparent-ish geometric longitude of the Sun (mean equinox of date, with aberration)."""
    t = (jd_tt - 2451545.0) / 36525.0
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    m = 357.52911 + 35999.05029 * t - 0.0001537 * t * t
    c = ((1.914602 - 0.004817 * t - 0.000014 * t * t) * _sin(m)
         + (0.019993 - 0.000101 * t) * _sin(2 * m) + 0.000289 * _sin(3 * m))
    aberration = 0.00569 if apparent else 0.0
    return norm360(l0 + c - aberration)


# ------------------------------------------------------------------------ Planets
# a, e, I, L, long.peri, long.node  and their rates per Julian century (J2000 ecliptic)
_ELEMENTS = {
    "Mercury": ((0.38709927, 0.20563593, 7.00497902, 252.25032350, 77.45779628, 48.33076593),
                (0.00000037, 0.00001906, -0.00594749, 149472.67411175, 0.16047689, -0.12534081)),
    "Venus": ((0.72333566, 0.00677672, 3.39467605, 181.97909950, 131.60246718, 76.67984255),
              (0.00000390, -0.00004107, -0.00078890, 58517.81538729, 0.00268329, -0.27769418)),
    "EMB": ((1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0.0),
            (0.00000562, -0.00004392, -0.01294668, 35999.37244981, 0.32327364, 0.0)),
    "Mars": ((1.52371034, 0.09339410, 1.84969142, -4.55343205, -23.94362959, 49.55953891),
             (0.00001847, 0.00007882, -0.00813131, 19140.30268499, 0.44441088, -0.29257343)),
    "Jupiter": ((5.20288700, 0.04838624, 1.30439695, 34.39644051, 14.72847983, 100.47390909),
                (-0.00011607, -0.00013253, -0.00183714, 3034.74612775, 0.21252668, 0.20469106)),
    "Saturn": ((9.53667594, 0.05386179, 2.48599187, 49.95424423, 92.59887831, 113.66242448),
               (-0.00125060, -0.00050991, 0.00193609, 1222.49362201, -0.41897216, -0.28867794)),
}


def _helio_xyz(name: str, t: float) -> tuple[float, float, float]:
    base, rate = _ELEMENTS[name]
    a, e, inc, L, wbar, node = (b + r * t for b, r in zip(base, rate))
    w = wbar - node
    M = norm360(L - wbar)
    if M > 180:
        M -= 360
    # Kepler's equation (degrees form)
    estar = e * R2D
    E = M + estar * _sin(M)
    for _ in range(30):
        dM = M - (E - estar * _sin(E))
        dE = dM / (1 - e * _cos(E))
        E += dE
        if abs(dE) < 1e-9:
            break
    xp = a * (_cos(E) - e)
    yp = a * math.sqrt(1 - e * e) * _sin(E)
    cw, sw, cO, sO, cI, sI = _cos(w), _sin(w), _cos(node), _sin(node), _cos(inc), _sin(inc)
    x = (cw * cO - sw * sO * cI) * xp + (-sw * cO - cw * sO * cI) * yp
    y = (cw * sO + sw * cO * cI) * xp + (-sw * sO + cw * cO * cI) * yp
    z = (sw * sI) * xp + (cw * sI) * yp
    return x, y, z


def planet_longitude_tropical(name: str, jd_tt: float, apparent: bool = False) -> float:
    """Geocentric ecliptic longitude, mean equinox of date (true geometric; light-time only in APPARENT mode)."""
    t = (jd_tt - 2451545.0) / 36525.0
    ex, ey, ez = _helio_xyz("EMB", t)
    px, py, pz = _helio_xyz(name, t)
    dx, dy, dz = px - ex, py - ey, pz - ez
    if apparent:
        # light-time + annual aberration ("planetary aberration"): both bodies taken at t − τ
        for _ in range(2):
            dist = math.sqrt(dx * dx + dy * dy + dz * dz)
            tt = t - dist * 0.0057755183 / 36525.0
            (px, py, pz), (qx, qy, qz) = _helio_xyz(name, tt), _helio_xyz("EMB", tt)
            dx, dy, dz = px - qx, py - qy, pz - qz
    lon_j2000 = math.atan2(dy, dx) * R2D
    return norm360(lon_j2000 + general_precession_arcsec(t) / 3600.0)


# ------------------------------------------------------------------------- Houses
def mean_obliquity(jd_tt: float) -> float:
    t = (jd_tt - 2451545.0) / 36525.0
    return 23.0 + 26.0 / 60 + (21.448 - 46.8150 * t - 0.00059 * t * t + 0.001813 * t**3) / 3600.0


def nutation(jd_tt: float) -> tuple[float, float]:
    """(Δψ, Δε) in degrees — IAU 1980 principal terms (~0.5\" accuracy)."""
    t = (jd_tt - 2451545.0) / 36525.0
    om = 125.04452 - 1934.136261 * t
    l = 280.4665 + 36000.7698 * t
    lp = 218.3165 + 481267.8813 * t
    dpsi = -17.20 * _sin(om) - 1.32 * _sin(2 * l) - 0.23 * _sin(2 * lp) + 0.21 * _sin(2 * om)
    deps = 9.20 * _cos(om) + 0.57 * _cos(2 * l) + 0.10 * _cos(2 * lp) - 0.09 * _cos(2 * om)
    return dpsi / 3600.0, deps / 3600.0


def gmst_deg(jd_ut: float) -> float:
    t = (jd_ut - 2451545.0) / 36525.0
    return norm360(280.46061837 + 360.98564736629 * (jd_ut - 2451545.0) + 0.000387933 * t * t - t**3 / 38710000.0)


def _ra_to_lon(ra: float, eps: float) -> float:
    return norm360(math.atan2(_sin(ra), _cos(ra) * _cos(eps)) * R2D)


def ascendant(ramc: float, eps: float, lat: float) -> float:
    return norm360(math.atan2(_cos(ramc), -(_sin(ramc) * _cos(eps) + math.tan(lat * D2R) * _sin(eps))) * R2D)


def midheaven(ramc: float, eps: float) -> float:
    return _ra_to_lon(ramc, eps)


def _placidus_cusp(ramc: float, eps: float, lat: float, frac: float, above: bool) -> float:
    """Iterate a Placidus intermediate cusp.
    above=True: houses 11/12 (frac of semi-diurnal arc from MC);
    above=False: houses 2/3 (frac of semi-nocturnal arc from IC)."""
    tphi = math.tan(lat * D2R)
    ra = ramc + (frac * 90.0 if above else 180.0 - frac * 90.0)
    for _ in range(100):
        lam = _ra_to_lon(ra, eps)
        dec = math.asin(_sin(eps) * _sin(lam)) * R2D
        x = -tphi * math.tan(dec * D2R)
        if abs(x) > 1:
            raise ValueError("Placidus undefined at this latitude")
        sda = math.acos(x) * R2D  # semi-diurnal arc
        new = ramc + frac * sda if above else ramc + 180.0 - frac * (180.0 - sda)
        if abs(((new - ra + 180) % 360) - 180) < 1e-9:
            ra = new
            break
        ra = new
    return _ra_to_lon(ra, eps)


def placidus_cusps(jd_ut: float, jd_tt: float, lat: float, lon: float) -> tuple[float, float, list[float]]:
    """Returns (ascendant, mc, cusps[1..12] as list index 0..11), tropical, true equinox of date
    (apparent sidereal time and true obliquity, as Swiss Ephemeris does)."""
    dpsi, deps = nutation(jd_tt)
    eps = mean_obliquity(jd_tt) + deps
    ramc = norm360(gmst_deg(jd_ut) + lon + dpsi * _cos(eps))
    asc = ascendant(ramc, eps, lat)
    mc = midheaven(ramc, eps)
    c11 = _placidus_cusp(ramc, eps, lat, 1 / 3, True)
    c12 = _placidus_cusp(ramc, eps, lat, 2 / 3, True)
    c2 = _placidus_cusp(ramc, eps, lat, 2 / 3, False)
    c3 = _placidus_cusp(ramc, eps, lat, 1 / 3, False)
    cusps = [asc, c2, c3, norm360(mc + 180), norm360(c11 + 180), norm360(c12 + 180),
             norm360(asc + 180), norm360(c2 + 180), norm360(c3 + 180), mc, c11, c12]
    return asc, mc, cusps


class BuiltinEngine(EphemerisEngine):
    name = "builtin"

    def _jd_tt(self, jd_ut: float) -> float:
        return jd_ut + delta_t_seconds(jd_ut) / 86400.0

    def ayanamsa(self, jd_ut: float, model: Ayanamsa) -> float:
        return ayanamsa_deg(self._jd_tt(jd_ut), model)

    def positions(self, jd_ut: float, model: Ayanamsa,
                  mode: PositionMode = DEFAULT_POSITION_MODE) -> dict[str, float]:
        jd_tt = self._jd_tt(jd_ut)
        ay = ayanamsa_deg(jd_tt, model)
        app = mode == PositionMode.APPARENT
        trop = {
            "Sun": sun_longitude_tropical(jd_tt, app),
            "Moon": moon_longitude_tropical(jd_tt),
        }
        for p in ("Mercury", "Venus", "Mars", "Jupiter", "Saturn"):
            trop[p] = planet_longitude_tropical(p, jd_tt, app)
        trop["Rahu"] = mean_node_tropical(jd_tt)
        trop["Ketu"] = norm360(trop["Rahu"] + 180)
        return {k: norm360(v - ay) for k, v in trop.items()}

    def houses(self, jd_ut: float, lat: float, lon: float, model: Ayanamsa) -> HouseResult:
        jd_tt = self._jd_tt(jd_ut)
        # cusps are on the true equinox; remove nutation as well as the (mean) ayanamsa
        ay = ayanamsa_deg(jd_tt, model) + nutation(jd_tt)[0]
        asc, mc, cusps = placidus_cusps(jd_ut, jd_tt, lat, lon)
        return HouseResult(
            ascendant=norm360(asc - ay),
            mc=norm360(mc - ay),
            cusps=[norm360(c - ay) for c in cusps],
        )
