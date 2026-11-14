#!/usr/bin/env python3
"""Download the real LOLA south-pole DEM (and optionally NASA's illumination maps).

    python scripts/astro/fetch_lola_dem.py                       # 80 m/px DEM, 181 MB
    python scripts/astro/fetch_lola_dem.py --res 40              # 40 m/px, 685 MB
    python scripts/astro/fetch_lola_dem.py --with-illumination   # + NASA validation maps, 59 MB

Files land in data/raw/dem/ and data/raw/illumination/ (git-ignored). Source: NASA PGDA,
"A New View of the Lunar South Pole from LOLA" (Barker et al. 2023), products 90 and 69.
With a non-default resolution, set LUNANAV_DEM_PATH to the downloaded file.
Needs: pip install rasterio  (for reading; this script itself only uses the standard library).
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEM_BASE = "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/"
ILL_BASE = "https://pgda.gsfc.nasa.gov/data/MoonIllumination/"
DEMS = {80: "LDEM_80S_80MPP_ADJ.TIF", 40: "LDEM_80S_40MPP_ADJ.TIF", 20: "LDEM_80S_20MPP_ADJ.TIF"}
ILLUM = ["AVGVISIB_85S_060M_201608.TIF", "AVGVISIB_85S_060M_201608_EARTH.TIF"]


def fetch(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        print(f"ok (already there) {dest}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    print(f"downloading {url}")
    with urllib.request.urlopen(url, timeout=60) as r, tmp.open("wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while chunk := r.read(1 << 20):
            f.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r  {done / 1e6:7.1f} / {total / 1e6:.1f} MB", end="", flush=True)
    print()
    tmp.replace(dest)
    print(f"saved {dest}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", type=int, choices=sorted(DEMS), default=80)
    ap.add_argument("--with-illumination", action="store_true")
    a = ap.parse_args()
    fetch(DEM_BASE + DEMS[a.res], REPO / "data" / "raw" / "dem" / DEMS[a.res])
    if a.with_illumination:
        for name in ILLUM:
            fetch(ILL_BASE + name, REPO / "data" / "raw" / "illumination" / name)
    if a.res != 80:
        print(f"set LUNANAV_DEM_PATH={REPO / 'data' / 'raw' / 'dem' / DEMS[a.res]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
