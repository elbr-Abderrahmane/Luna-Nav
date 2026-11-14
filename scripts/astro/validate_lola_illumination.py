#!/usr/bin/env python3
"""Check our terrain-aware illumination against NASA's published LOLA illumination maps.

Reference: PGDA "Lunar Polar Illumination" (Mazarico et al. 2011), average Sun visibility
(fraction of the solar disk visible, hourly over 18.6 years) and average Earth visibility
(any part of the Earth disk visible), 60 m/px, 85-90 deg S:
    AVGVISIB_85S_060M_201608.TIF, AVGVISIB_85S_060M_201608_EARTH.TIF
Ours: horizon mask from the LOLA DEM (lola_dem.py), Sun/Earth from the ephemeris, averaged over
`--years` years at `--step-h` steps.

    python scripts/astro/fetch_lola_dem.py --with-illumination
    python scripts/astro/validate_lola_illumination.py            # named sites + 30 random points
Writes data/validation/lola_illumination_check.csv and prints a summary.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

NAMED = {
    "connecting-ridge": (-89.45, -137.3),
    "shackleton-rim": (-89.68, -166.0),
    "shackleton-floor": (-89.66, 129.2),
    "south-pole": (-90.0, 0.0),
    "de-gerlache-rim": (-88.6, -68.0),
    "malapert-massif": (-85.95, 2.9),
}


def ref_value(ds, lat, lon):
    from rasterio.windows import Window

    from lunanav.astro.lola_dem import stereo

    x, y = stereo(lat, lon)
    t = ds.transform
    col, row = int((x - t.c) / t.a), int((y - t.f) / t.e)
    # median of the 3x3 pixels around the point: the NASA map has isolated 0-valued dropout
    # pixels (e.g. right on the connecting ridge), and 60 m pixels on a crest vary a lot
    w = ds.read(1, window=Window(col - 1, row - 1, 3, 3), boundless=True,
                fill_value=-32768).astype(float)
    w = w[w != -32768]
    return float("nan") if w.size == 0 else float(np.median(w)) * ds.scales[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=float, default=2.0)
    ap.add_argument("--step-h", type=float, default=3.0)
    ap.add_argument("--random", type=int, default=30)
    ap.add_argument("--start", default="2027-01-01T00:00:00Z")
    a = ap.parse_args()

    import rasterio

    from lunanav.astro.horizon import default_dem
    from lunanav.astro.scenarios import SiteModel
    from lunanav.astro.timeutil import to_utc

    dem = default_dem()
    if dem is None:
        print("no DEM: run scripts/astro/fetch_lola_dem.py first")
        return 1
    ill_dir = Path(os.environ.get("LUNANAV_ILLUM_DIR", REPO / "data" / "raw" / "illumination"))
    sun_ds = rasterio.open(ill_dir / "AVGVISIB_85S_060M_201608.TIF")
    earth_ds = rasterio.open(ill_dir / "AVGVISIB_85S_060M_201608_EARTH.TIF")

    t0 = to_utc(a.start)
    n = int(a.years * 365.25 * 24 / a.step_h)
    times = [t0 + timedelta(hours=k * a.step_h) for k in range(n)]

    rng = np.random.default_rng(7)
    pts = dict(NAMED)
    for i in range(a.random):
        # uniform in area inside 85.5-89.9 deg S
        lat = -math.degrees(math.acos(rng.uniform(math.cos(math.radians(89.9)),
                                                  math.cos(math.radians(85.5)))))
        pts[f"random-{i:02d}"] = (lat, float(rng.uniform(-180, 180)))

    rows = []
    for name, (lat, lon) in pts.items():
        site = SiteModel(lat, lon, dem=dem)
        if site.method != "horizon_mask":
            continue
        st = site.state(times)
        ours_sun = float(st["sun_frac"].mean())
        ours_earth = float((st["earth_margin"] > -st["earth_radius"]).mean())
        ref_sun, ref_earth = ref_value(sun_ds, lat, lon), ref_value(earth_ds, lat, lon)
        rows.append({"name": name, "lat_deg": round(lat, 4), "lon_deg": round(lon, 4),
                     "elevation_m": round(site.elevation_m, 1),
                     "sun_ours_pct": round(100 * ours_sun, 1),
                     "sun_nasa_pct": round(100 * ref_sun, 1),
                     "earth_ours_pct": round(100 * ours_earth, 1),
                     "earth_nasa_pct": round(100 * ref_earth, 1)})
        r = rows[-1]
        print(f"{name:18s} {lat:8.3f} {lon:8.2f}  sun ours {r['sun_ours_pct']:5.1f} % / NASA "
              f"{r['sun_nasa_pct']:5.1f} %   earth ours {r['earth_ours_pct']:5.1f} % / NASA "
              f"{r['earth_nasa_pct']:5.1f} %")

    out = Path(os.environ.get("LUNANAV_VALIDATION_DIR", REPO / "data" / "validation")) / "lola_illumination_check.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    s = np.array([[r["sun_ours_pct"], r["sun_nasa_pct"]] for r in rows])
    e = np.array([[r["earth_ours_pct"], r["earth_nasa_pct"]] for r in rows])
    for label, m in (("sun", s), ("earth", e)):
        d = m[:, 0] - m[:, 1]
        print(f"{label}: n={len(m)}  mean diff {d.mean():+.1f} pp  median |diff| "
              f"{np.median(np.abs(d)):.1f} pp  max |diff| {np.abs(d).max():.1f} pp  "
              f"correlation {np.corrcoef(m[:, 0], m[:, 1])[0, 1]:.3f}")
    print("wrote", out, "at", datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
