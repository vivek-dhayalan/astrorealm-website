from enum import Enum

from . import ashtakoota, kp, manglik, nodes, porutham


class Method(str, Enum):
    ASHTAKOOTA = "ASHTAKOOTA"
    PORUTHAM = "PORUTHAM"
    MANGLIK = "MANGLIK"
    RAHU_KETU = "RAHU_KETU"
    KP_7TH_CUSP = "KP_7TH_CUSP"


# response key, matcher, needs KP chart
REGISTRY = {
    Method.ASHTAKOOTA: ("ashtakoota", ashtakoota.match, False),
    Method.PORUTHAM: ("porutham", porutham.match, False),
    Method.MANGLIK: ("manglik", manglik.match, False),
    Method.RAHU_KETU: ("rahuKetu", nodes.match, False),
    Method.KP_7TH_CUSP: ("kp7thCusp", kp.match, True),
}
