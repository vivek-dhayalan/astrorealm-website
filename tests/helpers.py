"""Synthetic charts for rule tests (no ephemeris involved)."""
from app.core.ayanamsa import Ayanamsa
from app.core.chart import Chart, PlanetPos, house_of
from app.core.reference import nakshatra_index, pada, rashi_index, sub_lord

DEFAULT_POS = {"Sun": 100.0, "Mercury": 110.0, "Venus": 120.0, "Mars": 200.0,
               "Jupiter": 300.0, "Saturn": 330.0, "Rahu": 50.0}


def make_chart(moon: float, asc: float = 0.0, model: Ayanamsa = Ayanamsa.LAHIRI, **planets: float) -> Chart:
    pos = dict(DEFAULT_POS)
    pos.update(planets)
    pos["Moon"] = moon
    pos["Ketu"] = (pos["Rahu"] + 180) % 360
    cusps = [(asc + 30 * i) % 360 for i in range(12)]  # equal houses for synthetic charts
    pp = {n: PlanetPos(n, lng, rashi_index(lng), nakshatra_index(lng), pada(lng), sub_lord(lng), house_of(lng, cusps))
          for n, lng in pos.items()}
    return Chart(model, 0.0, "synthetic", 2451545.0, 13.0, 80.0, pp, asc, cusps)
