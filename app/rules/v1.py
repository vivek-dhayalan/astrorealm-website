"""Rule set v1 — every table and threshold the matchers use.

Traditions differ on several of these. Change values here (or add a v2 module)
rather than editing matcher code. Items marked VERIFY should be confirmed with
the astrologer.
"""
from __future__ import annotations

VERSION = "v1"

# Indices follow app.core.reference.NAKSHATRAS / RASHIS (0-based).
# ------------------------------------------------------------------ shared
# Natural (naisargika) planetary relationships, Parashara.
FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}
ENEMIES = {
    "Sun": {"Venus", "Saturn"},
    "Moon": set(),
    "Mars": {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus": {"Sun", "Moon"},
    "Saturn": {"Sun", "Moon", "Mars"},
}

# Gana by nakshatra: D = Deva, M = Manushya, R = Rakshasa
GANA = list("DMRMDMDDRRMMDRDRDRRMMDRRMMD")
GANA_NAMES = {"D": "Deva", "M": "Manushya", "R": "Rakshasa"}

# Yoni animal and gender per nakshatra
YONI = [
    ("Horse", "M"), ("Elephant", "M"), ("Sheep", "F"), ("Serpent", "M"), ("Serpent", "F"),
    ("Dog", "F"), ("Cat", "F"), ("Sheep", "M"), ("Cat", "M"), ("Rat", "M"),
    ("Rat", "F"), ("Cow", "M"), ("Buffalo", "F"), ("Tiger", "F"), ("Buffalo", "M"),
    ("Tiger", "M"), ("Deer", "F"), ("Deer", "M"), ("Dog", "M"), ("Monkey", "M"),
    ("Mongoose", "M"), ("Monkey", "F"), ("Lion", "F"), ("Horse", "F"), ("Lion", "M"),
    ("Cow", "F"), ("Elephant", "F"),
]
YONI_ANIMALS = ["Horse", "Elephant", "Sheep", "Serpent", "Dog", "Cat", "Rat",
                "Cow", "Buffalo", "Tiger", "Deer", "Monkey", "Mongoose", "Lion"]
YONI_SCORE = [  # symmetric; 0 = sworn enemies
    [4, 2, 2, 3, 2, 2, 2, 1, 0, 1, 3, 3, 2, 1],
    [2, 4, 3, 3, 2, 2, 2, 2, 3, 1, 2, 3, 2, 0],
    [2, 3, 4, 2, 1, 2, 1, 3, 3, 1, 2, 0, 3, 1],
    [3, 3, 2, 4, 2, 1, 1, 1, 1, 2, 2, 2, 0, 2],
    [2, 2, 1, 2, 4, 2, 1, 2, 2, 1, 0, 2, 1, 1],
    [2, 2, 2, 1, 2, 4, 0, 2, 2, 1, 3, 3, 2, 1],
    [2, 2, 1, 1, 1, 0, 4, 2, 2, 2, 2, 2, 1, 2],
    [1, 2, 3, 1, 2, 2, 2, 4, 3, 0, 3, 2, 2, 1],
    [0, 3, 3, 1, 2, 2, 2, 3, 4, 1, 2, 2, 2, 1],
    [1, 1, 1, 2, 1, 1, 2, 0, 1, 4, 1, 1, 2, 1],
    [3, 2, 2, 2, 0, 3, 2, 3, 2, 1, 4, 2, 2, 1],
    [3, 3, 0, 2, 2, 3, 2, 2, 2, 1, 2, 4, 3, 2],
    [2, 2, 3, 0, 1, 2, 1, 2, 2, 2, 2, 3, 4, 2],
    [1, 0, 1, 2, 1, 1, 2, 1, 1, 1, 1, 2, 2, 4],
]

# ------------------------------------------------------------- Ashtakoota
# Varna by rashi: 4 Brahmin, 3 Kshatriya, 2 Vaishya, 1 Shudra
VARNA = [3, 2, 1, 4, 3, 2, 1, 4, 3, 2, 1, 4]
VARNA_NAMES = {4: "Brahmin", 3: "Kshatriya", 2: "Vaishya", 1: "Shudra"}

# Vashya group by rashi; Dhanu and Makara split at 15°
# C = Chatushpada, N = Nara/Manava, J = Jalachara, V = Vanachara, K = Keeta
VASHYA_BY_RASHI = ["C", "C", "N", "J", "V", "N", "N", "K", ("N", "C"), ("C", "J"), "N", "J"]
VASHYA_NAMES = {"C": "Chatushpada", "N": "Manava", "J": "Jalachara", "V": "Vanachara", "K": "Keeta"}
VASHYA_ORDER = "CNJVK"
VASHYA_SCORE = [  # boy row, girl column — VERIFY (several published variants)
    [2, 1, 1, 0.5, 1],
    [1, 2, 0.5, 0, 1],
    [1, 0.5, 2, 1, 1],
    [0.5, 0, 1, 2, 0],
    [1, 1, 1, 0, 2],
]

TARA_BAD = {3, 5, 7}  # Vipat, Pratyak, Naidhana

GANA_SCORE = {  # (boy, girl)
    ("D", "D"): 6, ("D", "M"): 6, ("D", "R"): 0,
    ("M", "D"): 5, ("M", "M"): 6, ("M", "R"): 0,
    ("R", "D"): 1, ("R", "M"): 0, ("R", "R"): 6,
}

BHAKOOT_BAD_PAIRS = [{2, 12}, {5, 9}, {6, 8}]

# Nadi by nakshatra: A = Adi (Vata), M = Madhya (Pitta), N = Antya (Kapha)
NADI = list("AMNNMAAMNNMAAMNNMAAMNNMAAMN")
NADI_NAMES = {"A": "Adi", "M": "Madhya", "N": "Antya"}

# Cancelled doshas whose koota gets full points back (astrologer, 2026-10-02: Bhakoot only)
ASHTAKOOTA_RESTORE_ON_CANCEL = {"Bhakoot"}

ASHTAKOOTA_BANDS = [  # (min total inclusive, result, label)
    (33, "ATI_UTTAMAM", "Excellent"),
    (25, "UTTAMAM", "Good"),
    (18, "MADHYAMAM", "Average"),
    (0, "ADHAMAM", "Poor / not recommended"),
]

# ---------------------------------------------------------------- Porutham
# Counts are inclusive, from the girl's star/rasi to the boy's.
DINA_MATCH_COUNTS = {2, 4, 6, 8, 9, 11, 13, 15, 18, 20, 24, 26}
DINA_PARTIAL_COUNTS = {1}  # same nakshatra — VERIFY (accepted for some stars only)
MAHENDRA_COUNTS = {4, 7, 10, 13, 16, 19, 22, 25}
STREE_DEERGHA_MATCH_MIN = 14     # count >= 14 → MATCH  (i.e. "beyond 13")
STREE_DEERGHA_PARTIAL_MIN = 8    # 8..13 → PARTIAL — VERIFY (some use 9)
RASI_MATCH_COUNTS = {1, 7, 9, 10, 11}   # VERIFY
RASI_PARTIAL_COUNTS = {12}              # dwirdwadasa — VERIFY
# Rasi count 1 with the *same* nakshatra is downgraded to PARTIAL.

# Vasya (rasi-based): rashi → rashis that are vasya to it
VASYA = {
    0: {4, 7}, 1: {3, 6}, 2: {5}, 3: {7, 8}, 4: {6}, 5: {2, 11},
    6: {5, 9}, 7: {3}, 8: {11}, 9: {0, 10}, 10: {0}, 11: {9},
}

# Rajju group per nakshatra
RAJJU = ["Pada", "Kati", "Nabhi", "Kantha", "Siro", "Kantha", "Nabhi", "Kati", "Pada",
         "Pada", "Kati", "Nabhi", "Kantha", "Siro", "Kantha", "Nabhi", "Kati", "Pada",
         "Pada", "Kati", "Nabhi", "Kantha", "Siro", "Kantha", "Nabhi", "Kati", "Pada"]

# Vedha pairs (nakshatra indices)
VEDHA_PAIRS = [
    (0, 17), (1, 16), (2, 15), (3, 14), (5, 21), (6, 20), (7, 19), (8, 18),
    (9, 26), (10, 25), (11, 24), (12, 23), (4, 22), (4, 13), (13, 22),
]

# Grading (astrologer's rule, 12 poruthams):
#   REJECTED  — any PORUTHAM_CRITICAL fails
#   UTTAMAM   — every porutham in PORUTHAM_UTTAMAM_REQUIRED matches
#   MADHYAMAM — every porutham in PORUTHAM_MADHYAMAM_REQUIRED matches
#   ADHAMAM   — otherwise
PORUTHAM_CRITICAL = ["Nadi", "Vedha"]          # confirmed by the astrologer (2026-10-02)
# Same-nadi exceptions (same star/different rashi, same star/different pada, same rashi/different star)
# turn a same-nadi Nadi porutham into a MATCH (and so it no longer rejects)
PORUTHAM_NADI_EXCEPTIONS = True
PORUTHAM_UTTAMAM_REQUIRED = ["Rajju", "Varna", "Nadi", "Rasi", "Rasyadhipathi", "Stree Deergha"]
PORUTHAM_MADHYAMAM_REQUIRED = ["Rajju"]
PORUTHAM_LABELS = {"UTTAMAM": "Excellent", "MADHYAMAM": "Average", "ADHAMAM": "Poor"}

# ------------------------------------------------------------ Mangal dosha
MANGLIK_HOUSES = {1, 2, 4, 7, 8, 12}
MARS_OWN_OR_EXALTED = {0, 7, 9}  # Mesha, Vrishchika, Makara
# (house from reference, rashi of Mars) combinations that cancel the dosha
MANGLIK_HOUSE_SIGN_EXCEPTIONS = {
    2: {2, 5},      # 2nd in Mithuna/Kanya
    4: {0, 7},      # 4th in Mesha/Vrishchika
    7: {3, 9},      # 7th in Karka/Makara
    8: {8, 11},     # 8th in Dhanu/Meena
    12: {1, 6},     # 12th in Vrishabha/Tula
}
MANGLIK_CANCEL_CONJUNCT = {"Jupiter", "Moon"}

# -------------------------------------------------------------------- KP
KP_GOOD_HOUSES = {2, 7, 11}
KP_BAD_HOUSES = {1, 6, 10}
KP_SENSITIVITY_MINUTES = 5
# HOUSE_SIGNIFICATORS matches the astrologer's software (AstroWonder); FOUR_LEVEL is the textbook union
KP_SIGNIFICATION_METHOD = "HOUSE_SIGNIFICATORS"
