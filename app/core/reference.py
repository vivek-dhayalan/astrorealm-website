"""Static Vedic reference data: rashis, nakshatras, lords, Vimshottari sequence."""
from __future__ import annotations

NAKSHATRA_SPAN = 360.0 / 27.0  # 13°20'
PADA_SPAN = NAKSHATRA_SPAN / 4.0  # 3°20'
RASHI_SPAN = 30.0

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

RASHIS = [
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena",
]
RASHI_ENGLISH = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
RASHI_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

# Vimshottari dasha order and years (also the KP sub-division order)
VIMSHOTTARI = [
    ("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10), ("Mars", 7),
    ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17),
]
VIMSHOTTARI_TOTAL = 120

NAKSHATRA_LORDS = [VIMSHOTTARI[i % 9][0] for i in range(27)]


def norm360(x: float) -> float:
    x = x % 360.0
    return x + 360.0 if x < 0 else x


def rashi_index(lon: float) -> int:
    return int(norm360(lon) // RASHI_SPAN) % 12


def nakshatra_index(lon: float) -> int:
    return int(norm360(lon) // NAKSHATRA_SPAN) % 27


def pada(lon: float) -> int:
    within = norm360(lon) % NAKSHATRA_SPAN
    return int(within // PADA_SPAN) + 1


def sub_lord(lon: float) -> str:
    """KP sub-lord: the nakshatra divided into 9 Vimshottari-proportional parts,
    starting from the nakshatra's own lord."""
    lon = norm360(lon)
    nak = nakshatra_index(lon)
    within = lon - nak * NAKSHATRA_SPAN
    start = nak % 9
    acc = 0.0
    for k in range(9):
        lord, years = VIMSHOTTARI[(start + k) % 9]
        acc += years / VIMSHOTTARI_TOTAL * NAKSHATRA_SPAN
        if within < acc - 1e-12:
            return lord
    return VIMSHOTTARI[(start + 8) % 9][0]


def kp_lords(lon: float, depth: int = 4) -> list[str]:
    """KP lords at successive levels: [star, sub, sub-sub, sub-sub-sub, ...].
    Each level splits the previous span into 9 Vimshottari-proportional parts,
    starting from that level's lord."""
    lon = norm360(lon)
    nak = nakshatra_index(lon)
    within = lon - nak * NAKSHATRA_SPAN
    span = NAKSHATRA_SPAN
    start = nak % 9
    lords = [VIMSHOTTARI[start][0]]
    for _ in range(depth - 1):
        acc = 0.0
        chosen = (start + 8) % 9
        part_start, part_len = span - VIMSHOTTARI[chosen][1] / VIMSHOTTARI_TOTAL * span, VIMSHOTTARI[chosen][1] / VIMSHOTTARI_TOTAL * span
        for k in range(9):
            idx = (start + k) % 9
            length = VIMSHOTTARI[idx][1] / VIMSHOTTARI_TOTAL * span
            if within < acc + length - 1e-12:
                chosen, part_start, part_len = idx, acc, length
                break
            acc += length
        lords.append(VIMSHOTTARI[chosen][0])
        within -= part_start
        span = part_len
        start = chosen
    return lords


def distance_to_boundary(lon: float, span: float) -> float:
    """Degrees from lon to the nearest multiple of span."""
    r = norm360(lon) % span
    return min(r, span - r)


def count_inclusive(from_idx: int, to_idx: int, n: int) -> int:
    """Traditional inclusive count from one sign/star to another (1..n)."""
    return ((to_idx - from_idx) % n) + 1
