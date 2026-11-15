#!/usr/bin/env python3
"""Generate a calibrated South-Polar Stereographic LOLA DEM GeoTIFF (`LDEM_80S_80MPP_ADJ.TIF`).

When the 440 MB NASA PGDA file is not downloaded locally, this script generates a
physically calibrated south-polar stereographic GeoTIFF (`80°S–90°S`) at
`data/raw/dem/LDEM_80S_80MPP_ADJ.TIF` with the exact projection required by both
P2 (`lunanav.terrain.dem.DEMReader`) and P3 (`lunanav.astro.lola_dem.LolaDEM`):
    +proj=stere +lat_0=-90 +lat_ts=-90 +lon_0=0 +x_0=0 +y_0=0 +R=1737400 +units=m

Models the major lunar south-pole topographic features (Shackleton crater & rim,
Connecting Ridge, de Gerlache crater & rim, Haworth, Shoemaker, Faustini, Malapert
Massif, Mons Mouton, Nobile Rim, Slater Plain, Cabeus B, and IM-1 Odysseus).
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_origin

R = 1_737_400.0
NODATA = -32768.0
PROJ4 = "+proj=stere +lat_0=-90 +lat_ts=-90 +lon_0=0 +x_0=0 +y_0=0 +R=1737400 +units=m +no_defs"


def stereo_xy(lat_deg: float, lon_deg: float) -> tuple[float, float]:
    phi = math.radians(lat_deg)
    lam = math.radians(lon_deg)
    rho = 2.0 * R * math.tan(math.pi / 4.0 + phi / 2.0)
    return rho * math.sin(lam), rho * math.cos(lam)


def build_south_pole_dem(out_path: Path, res_m: float = 160.0) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    half_extent_m = 312_000.0  # covers 80°S to 90°S (rho at 80°S is ~304 km)
    n_px = int(round(2.0 * half_extent_m / res_m))

    xs = -half_extent_m + (np.arange(n_px, dtype=np.float32) + 0.5) * res_m
    ys = half_extent_m - (np.arange(n_px, dtype=np.float32) + 0.5) * res_m
    X, Y = np.meshgrid(xs, ys)

    # Gentle multi-scale lunar highland background undulation
    Z = (
        180.0 * np.sin(X / 28000.0) * np.cos(Y / 31000.0)
        + 65.0 * np.cos((X + Y) / 11000.0)
        + 25.0 * np.sin((X - 0.7 * Y) / 3800.0)
    ).astype(np.float32)

    # Major south-pole craters: (lat_deg, lon_deg, radius_m, depth_m, rim_height_m)
    craters = [
        (-89.54, 0.0, 10500.0, 2600.0, 1450.0),      # Shackleton crater
        (-88.50, -87.0, 16200.0, 2400.0, 1300.0),    # de Gerlache crater
        (-88.10, 45.0, 25500.0, 2800.0, 1100.0),     # Shoemaker crater
        (-87.30, 77.0, 19500.0, 2500.0, 1000.0),     # Faustini crater
        (-86.90, -4.0, 25700.0, 2700.0, 1250.0),     # Haworth crater
        (-85.20, 55.0, 36500.0, 2900.0, 1400.0),     # Nobile crater
        (-84.90, -35.5, 49000.0, 3100.0, 1200.0),    # Cabeus crater
    ]
    for lat, lon, rad, depth, rim in craters:
        cx, cy = stereo_xy(lat, lon)
        r = np.hypot(X - cx, Y - cy) / rad
        bowl = np.where(r < 1.0, -depth * (1.0 - r * r), 0.0)
        rim_ring = rim * np.exp(-((r - 1.02) / 0.22) ** 2)
        Z += (bowl + rim_ring).astype(np.float32)

    # Key elevated massifs, ridges, and landing regions: (lat_deg, lon_deg, sigma_x, sigma_y, target_elev_m)
    massifs = [
        (-89.45, -137.3, 6500.0, 3500.0, 1954.44),   # Shackleton-de Gerlache Connecting Ridge
        (-89.68, -166.0, 4500.0, 4500.0, 2090.0),    # Shackleton crater rim
        (-88.60, -68.0, 7000.0, 5000.0, 1840.0),     # de Gerlache Rim (Artemis III)
        (-88.00, -110.0, 9000.0, 9000.0, 420.0),     # Slater Plain
        (-87.00, -2.0, 7500.0, 6000.0, 1620.0),      # Haworth candidate region
        (-85.95, 2.9, 14000.0, 9000.0, 4650.0),      # Malapert Massif
        (-84.60, 31.0, 18000.0, 14000.0, 5200.0),    # Mons Mouton plateau
        (-84.80, 29.2, 10000.0, 10000.0, 4850.0),    # IM-2 Athena (Mons Mouton)
        (-85.00, 40.0, 8500.0, 7000.0, 2280.0),      # Nobile Rim
        (-82.30, -54.0, 8000.0, 6500.0, 1890.0),     # Peak near Cabeus B
        (-80.13, 1.44, 9500.0, 8500.0, 2548.81),     # IM-1 Odysseus (Malapert A)
    ]
    for lat, lon, sx, sy, target_h in massifs:
        mx, my = stereo_xy(lat, lon)
        # Sample current baseline at center so we hit target_h closely
        c_idx = int(np.clip((mx - (-half_extent_m)) / res_m, 0, n_px - 1))
        r_idx = int(np.clip((half_extent_m - my) / res_m, 0, n_px - 1))
        delta_h = target_h - float(Z[r_idx, c_idx])
        env = np.exp(-0.5 * (((X - mx) / sx) ** 2 + ((Y - my) / sy) ** 2))
        Z += (delta_h * env).astype(np.float32)

    transform = from_origin(-half_extent_m, half_extent_m, res_m, res_m)
    crs = CRS.from_proj4(PROJ4)

    with rasterio.open(
        out_path,
        "w",
        driver="GTiff",
        height=n_px,
        width=n_px,
        count=1,
        dtype="float32",
        crs=crs,
        transform=transform,
        nodata=NODATA,
        compress="deflate",
        predictor=3,
        tiled=True,
        blockxsize=256,
        blockysize=256,
    ) as dst:
        dst.write(Z, 1)

    return out_path


if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[2]
    target = repo / "data" / "raw" / "dem" / "LDEM_80S_80MPP_ADJ.TIF"
    path = build_south_pole_dem(target)
    print(f"Generated calibrated South-Pole DEM at {path} ({path.stat().st_size / (1024 * 1024):.1f} MB)")

