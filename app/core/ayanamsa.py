"""Ayanamsa models for the built-in engine (Swiss Ephemeris computes its own).

Both models follow the Swiss Ephemeris definitions: a reference epoch value
carried forward with IAU 2006 general precession in longitude.
"""
from __future__ import annotations

from enum import Enum


class Ayanamsa(str, Enum):
    LAHIRI = "LAHIRI"
    KP = "KP"


# (reference JD, ayanamsa at that epoch in degrees)
_DEFS = {
    Ayanamsa.LAHIRI: (2435553.5, 23.250182778 - 0.004658035),  # 1956-03-21
    Ayanamsa.KP: (2415020.0, 22.363889),  # J1900, Krishnamurti
}


def general_precession_arcsec(t_centuries: float) -> float:
    """Accumulated general precession in longitude since J2000 (IAU 2006)."""
    t = t_centuries
    return 5028.796195 * t + 1.1054348 * t * t + 0.00007964 * t**3


def ayanamsa_deg(jd_tt: float, model: Ayanamsa) -> float:
    jd0, a0 = _DEFS[model]
    t = (jd_tt - 2451545.0) / 36525.0
    t0 = (jd0 - 2451545.0) / 36525.0
    return a0 + (general_precession_arcsec(t) - general_precession_arcsec(t0)) / 3600.0
