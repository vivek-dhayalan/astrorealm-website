"""Engine selection: Swiss Ephemeris if importable, else the built-in engine.
Override with MATCHAPI_ENGINE=builtin|swisseph."""
from __future__ import annotations

import os
from functools import lru_cache

from .base import EphemerisEngine, HouseResult
from .builtin import BuiltinEngine


@lru_cache(maxsize=4)
def get_engine(name: str | None = None) -> EphemerisEngine:
    name = (name or os.environ.get("MATCHAPI_ENGINE") or "auto").lower()
    if name in ("auto", "swisseph"):
        try:
            from .swiss import SwissEngine

            return SwissEngine()
        except ImportError:
            if name == "swisseph":
                raise
    return BuiltinEngine()


__all__ = ["get_engine", "EphemerisEngine", "HouseResult", "BuiltinEngine"]
