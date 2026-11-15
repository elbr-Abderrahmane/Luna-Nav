"""Optional descriptive local terrain metrics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from lunanav.terrain.dem import DEMReader, site_coverage
from lunanav.terrain.heightmap import extract_heightmap


def _array_for_site(lat_deg: float, lon_deg: float, radius_m: float,
                    dem_path: str | Path | None) -> tuple[dict[str, Any], np.ndarray]:
    result = extract_heightmap(lat_deg, lon_deg, radius_m, dem_path)
    values = np.array([
        [np.nan if v is None else float(v) for v in row]
        for row in result.get("values_m", [])
    ], dtype=float)
    return result, values


def terrain_summary(lat_deg: float, lon_deg: float, radius_m: float = 240.0,
                    dem_path: str | Path | None = None) -> dict[str, Any]:
    """Return valid elevation count and descriptive statistics in metres."""
    result, arr = _array_for_site(lat_deg, lon_deg, radius_m, dem_path)
    valid = arr[np.isfinite(arr)]
    if valid.size == 0:
        return {"status": result["status"], "valid_pixel_count": 0,
                "min_elevation_m": None, "max_elevation_m": None,
                "mean_elevation_m": None, "roughness_m": None}
    return {
        "status": "ok", "valid_pixel_count": int(valid.size),
        "min_elevation_m": float(valid.min()), "max_elevation_m": float(valid.max()),
        "mean_elevation_m": float(valid.mean()), "roughness_m": float(valid.std()),
    }


def local_roughness(lat_deg: float, lon_deg: float, radius_m: float = 240.0,
                    dem_path: str | Path | None = None) -> dict[str, Any]:
    """Return standard deviation of valid local elevations, in metres."""
    summary = terrain_summary(lat_deg, lon_deg, radius_m, dem_path)
    return {"status": summary["status"], "roughness_m": summary["roughness_m"],
            "valid_pixel_count": summary["valid_pixel_count"]}


def local_slope(lat_deg: float, lon_deg: float, dem_path: str | Path | None = None
                ) -> dict[str, Any]:
    """Estimate center-pixel slope in degrees using a 3x3 Horn neighborhood."""
    coverage = site_coverage(lat_deg, lon_deg, dem_path)
    if not coverage["pixel_covered"]:
        return {"status": coverage["status"], "slope_deg": None}
    path = Path(dem_path) if dem_path is not None else None
    with DEMReader(path) as reader:
        ds = reader.dataset
        row, col = coverage["row"], coverage["col"]
        if row == 0 or col == 0 or row >= ds.height-1 or col >= ds.width-1:
            return {"status": "insufficient_neighborhood", "slope_deg": None}
        block = ds.read(1, window=((row-1, row+2), (col-1, col+2)), masked=True)
        if np.ma.getmaskarray(block).any() or not np.isfinite(block.filled(np.nan)).all():
            return {"status": "nodata_neighborhood", "slope_deg": None}
        z = np.asarray(block, dtype=float)
        dx, dy = abs(float(ds.transform.a)), abs(float(ds.transform.e))
        dzdx = ((z[0, 2] + 2*z[1, 2] + z[2, 2]) -
                (z[0, 0] + 2*z[1, 0] + z[2, 0])) / (8*dx)
        dzdy = ((z[2, 0] + 2*z[2, 1] + z[2, 2]) -
                (z[0, 0] + 2*z[0, 1] + z[0, 2])) / (8*dy)
        slope = float(np.degrees(np.arctan(np.hypot(dzdx, dzdy))))
        return {"status": "ok", "slope_deg": slope}
