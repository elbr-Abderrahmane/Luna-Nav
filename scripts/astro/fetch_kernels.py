#!/usr/bin/env python3
"""Download the NAIF SPICE kernels used by the `spice` ephemeris backend (README §5, P3 brief).

    python scripts/astro/fetch_kernels.py            # into data/raw/kernels/ (gitignored)
    python scripts/astro/fetch_kernels.py --dir /some/where

Kernels: leap seconds (LSK), DE440s planetary ephemeris (SPK, ~32 MB), the DE440 lunar PA
orientation (binary PCK) and the lunar frame kernel defining MOON_ME / MOON_PA (FK).
The newest file matching each pattern is picked from the NAIF directory listing, then a
metakernel `lunanav.tm` is written. Never commit kernels.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path

BASE = "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/"
WANTED = [  # (directory, filename regex)
    ("lsk/", r"naif\d{4}\.tls"),
    ("spk/planets/", r"de440s\.bsp"),
    ("pck/", r"moon_pa_de440_\d{6}\.bpc"),
    ("fk/satellites/", r"moon_de440_\d{6}\.tf"),
]
REPO = Path(__file__).resolve().parents[2]


def newest(dir_url: str, pattern: str) -> str:
    html = urllib.request.urlopen(dir_url, timeout=60).read().decode("latin-1")
    names = sorted(set(re.findall(rf'href="({pattern})"', html)))
    if not names:
        raise SystemExit(f"nothing matching {pattern} at {dir_url}")
    return names[-1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, default=REPO / "data" / "raw" / "kernels")
    args = ap.parse_args()
    args.dir.mkdir(parents=True, exist_ok=True)
    files = []
    for sub, pat in WANTED:
        name = newest(BASE + sub, pat)
        dest = args.dir / name
        if not dest.exists():
            print(f"downloading {sub}{name} …", flush=True)
            tmp = dest.with_suffix(dest.suffix + ".part")
            urllib.request.urlretrieve(BASE + sub + name, tmp)
            tmp.replace(dest)
        else:
            print(f"have {name}")
        files.append(dest)
    tm = args.dir / "lunanav.tm"
    lines = ",\n".join(f"    '{f.name}'" for f in files)
    tm.write_text(
        "KPL/MK\n\\begindata\n"
        f"PATH_VALUES = ( '{args.dir.resolve()}' )\nPATH_SYMBOLS = ( 'K' )\n"
        "KERNELS_TO_LOAD = (\n" + lines.replace("    '", "    '$K/") + "\n)\n\\begintext\n"
    )
    print(f"wrote {tm}. The astro module now uses SPICE automatically (LUNANAV_EPHEMERIS=auto).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
