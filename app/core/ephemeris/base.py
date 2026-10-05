from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from ..ayanamsa import Ayanamsa


class PositionMode(str, Enum):
    TRUE = "TRUE"          # true geometric positions (no light-time / aberration) — what AstroWonder prints
    APPARENT = "APPARENT"  # apparent positions, as seen from Earth (Swiss Ephemeris default)


DEFAULT_POSITION_MODE = PositionMode(os.environ.get("MATCHAPI_POSITIONS", "TRUE").upper())
POSITION_MODE = DEFAULT_POSITION_MODE.value  # backwards-compatible name


@dataclass
class HouseResult:
    ascendant: float          # sidereal degrees
    mc: float                 # sidereal degrees
    cusps: list[float]        # Placidus cusps 1..12 (index 0 = 1st), sidereal


class EphemerisEngine(ABC):
    name: str = "abstract"

    @abstractmethod
    def ayanamsa(self, jd_ut: float, model: Ayanamsa) -> float: ...

    @abstractmethod
    def positions(self, jd_ut: float, model: Ayanamsa,
                  mode: PositionMode = DEFAULT_POSITION_MODE) -> dict[str, float]:
        """Sidereal ecliptic longitudes for Sun..Saturn, Rahu (mean node), Ketu."""

    @abstractmethod
    def houses(self, jd_ut: float, lat: float, lon: float, model: Ayanamsa) -> HouseResult: ...
