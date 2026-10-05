"""Download GeoNames dumps and build data/geonames.sqlite.

Usage:
    python scripts/build_geonames.py                 # download + build
    python scripts/build_geonames.py --raw-dir DIR   # use already-downloaded files
    python scripts/build_geonames.py --countries IN,LK --no-world

Data © GeoNames (https://www.geonames.org), licensed CC BY 4.0.
"""
from __future__ import annotations

import argparse
import io
import sys
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.geo.store import GeoStore, normalize  # noqa: E402

BASE = "https://download.geonames.org/export/dump/"
UA = "MatchAPI/0.1 geonames-builder"
MAX_ALT_NAMES = 25


def fetch(name: str, raw_dir: Path) -> Path:
    dest = raw_dir / name
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  using cached {dest.name}")
        return dest
    print(f"  downloading {name} ...", flush=True)
    req = urllib.request.Request(BASE + name, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as fh:
        while chunk := resp.read(1 << 20):
            fh.write(chunk)
    return dest


def read_text(path: Path, inner: str | None = None) -> io.TextIOBase:
    if path.suffix == ".zip":
        zf = zipfile.ZipFile(path)
        member = inner or next(n for n in zf.namelist() if n.endswith(".txt") and "readme" not in n.lower())
        return io.TextIOWrapper(zf.open(member), encoding="utf-8")
    return open(path, encoding="utf-8")


def load_admin1(path: Path) -> dict[str, str]:
    out = {}
    with read_text(path) as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2:
                out[parts[0]] = parts[1]
    return out


def load_countries(path: Path) -> dict[str, str]:
    out = {}
    with read_text(path) as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) > 4:
                out[parts[0]] = parts[4]
    return out


def ingest(store: GeoStore, path: Path, admin1: dict, countries: dict, seen: set[int]) -> int:
    rows, names, n = [], [], 0
    with read_text(path) as fh:
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) < 19 or f[6] != "P":
                continue
            gid = int(f[0])
            if gid in seen:
                continue
            seen.add(gid)
            cc = f[8]
            rows.append((gid, f[1], admin1.get(f"{cc}.{f[10]}"), cc, countries.get(cc),
                         float(f[4]), float(f[5]), f[17] or None, int(f[14] or 0), f[7]))
            norms = {normalize(f[1]), normalize(f[2])}
            for alt in f[3].split(",")[: MAX_ALT_NAMES * 4]:
                a = normalize(alt)
                if len(a) >= 3:
                    norms.add(a)
                if len(norms) >= MAX_ALT_NAMES:
                    break
            names.extend((x, gid) for x in norms if x)
            n += 1
            if len(rows) >= 20000:
                store.insert_places(rows, names)
                rows, names = [], []
    if rows:
        store.insert_places(rows, names)
    return n


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw-dir", default=str(ROOT / "data" / "raw"))
    ap.add_argument("--db", default=str(ROOT / "data" / "geonames.sqlite"))
    ap.add_argument("--countries", default="IN", help="Comma-separated full-country dumps (villages included)")
    ap.add_argument("--no-world", action="store_true", help="Skip cities500 (worldwide, pop >= 500)")
    args = ap.parse_args()

    raw = Path(args.raw_dir)
    raw.mkdir(parents=True, exist_ok=True)
    db = Path(args.db)
    tmp = db.with_suffix(".building")
    if tmp.exists():
        tmp.unlink()

    t0 = time.time()
    print("Fetching GeoNames files")
    admin1 = load_admin1(fetch("admin1CodesASCII.txt", raw))
    countries = load_countries(fetch("countryInfo.txt", raw))
    sources = [fetch(f"{c.strip().upper()}.zip", raw) for c in args.countries.split(",") if c.strip()]
    if not args.no_world:
        sources.append(fetch("cities500.zip", raw))

    store = GeoStore(tmp, create=True)
    seen: set[int] = set()
    for src in sources:
        print(f"Loading {src.name} ...", flush=True)
        print(f"  {ingest(store, src, admin1, countries, seen):,} populated places")
    print("Indexing ...", flush=True)
    store.finalize({
        "built_at": datetime.now(timezone.utc).isoformat(),
        "sources": ",".join(s.name for s in sources),
        "attribution": "GeoNames (geonames.org), CC BY 4.0",
    })
    store.conn.close()
    if db.exists():
        db.unlink()
    tmp.rename(db)
    print(f"Done: {db} ({db.stat().st_size / 1e6:.1f} MB, {len(seen):,} places) in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
