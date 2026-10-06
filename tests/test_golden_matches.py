"""Regression against astrologer-validated pair results (tests/fixtures/golden_matches.json).

Only the methods listed in a case's "verified" are asserted. Moon-based methods (Ashtakoota,
Porutham) are checked on every engine; lagna, Manglik and KP 7th cusp are time-sensitive and
only checked on Swiss Ephemeris."""
import json
from pathlib import Path

import pytest

from app.core.ephemeris import get_engine
from app.schemas import MatchRequest
from app.service import run_match

# Real couples' validated results: kept out of the public repo (tests/fixtures/private/ is git-ignored)
_FILE = Path(__file__).parent / "fixtures" / "private" / "golden_matches.json"
CASES = json.loads(_FILE.read_text(encoding="utf-8"))["matches"] if _FILE.exists() else []


@pytest.mark.skipif(not CASES, reason="Private validated matches not present")
@pytest.mark.parametrize("case", CASES or [None], ids=[c["label"] for c in CASES] or ["none"])
def test_golden_match(case):
    r = run_match(MatchRequest(**case["request"]))
    exp, verified = case["expected"], set(case["verified"])

    for side in ("boy", "girl"):
        for k, v in exp[side].items():
            assert r[side][k] == v, f"{side}.{k}"

    if "ashtakoota" in verified:
        a, ea = r["ashtakoota"], exp["ashtakoota"]
        assert a["result"] == ea["result"]
        assert a["score"]["total"] == ea["total"]
        assert a["score"]["rawTotal"] == ea["rawTotal"]
        kootas = {k["name"]: k for k in a["details"]["kootas"]}
        assert {n: kootas[n]["score"] for n in ea["kootas"]} == ea["kootas"]
        if "bhakootRaw" in ea:
            assert kootas["Bhakoot"]["rawScore"] == ea["bhakootRaw"]

    if "porutham" in verified:
        for view in ("strict", "lenient"):
            got, want = r["porutham"]["score"][view], exp["porutham"][view]
            assert {k: got[k] for k in want} == want, view

    if get_engine().name != "swisseph":
        return
    sw = exp.get("swissephOnly", {})
    for side, lagna in sw.get("lagna", {}).items():
        assert r[side]["lagna"] == lagna, f"{side}.lagna"
    if "manglik" in verified:
        m, em = r["manglik"], sw["manglik"]
        assert m["result"] == em["result"]
        legacy = {"HIGH": "STRONG", "LOW": "MILD"}  # fixture written with the old status names
        assert m["details"]["south"]["boy"]["status"] == legacy.get(em["boy"], em["boy"])
        assert m["details"]["south"]["girl"]["status"] == legacy.get(em["girl"], em["girl"])
    if "kp7thCusp" in verified:
        k, ek = r["kp7thCusp"], sw["kp7thCusp"]
        assert k["result"] == ek["result"]
        for side in ("boy", "girl"):
            for f, v in ek[side].items():
                assert k["details"][side][f] == v, f"kp {side}.{f}"
