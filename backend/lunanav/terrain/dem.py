"""Read-only access to the project's lunar LOLA DEM."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from rasterio.transform import rowcol

from lunanav.astro.lola_dem import NODATA, LolaDEM, load_default
from lunanav.coords import (
    MOON_RADIUS_M, PROJ4_SOUTH_POLAR, is_nominal_dem_latitude, latlon_to_xy,
    normalize_latlon,
)

EXPECTED_DEM_NAME = "LDEM_80S_80MPP_ADJ.TIF"


def repository_root() -> Path:
    """Infer repository root from backend/lunanav/terrain/dem.py location."""
    return Path(__file__).resolve().parents[3]


def default_dem_path() -> Path:
    """Return the required repository-relative DEM path, with optional override."""
    override = os.environ.get("LUNANAV_DEM_PATH")
    return Path(override).expanduser() if override else (
        repository_root() / "data" / "raw" / "dem" / EXPECTED_DEM_NAME
    )


def _json_number(value: Any) -> float | int | None:
    """Convert a NumPy scalar to a JSON-safe Python scalar."""
    if value is None:
        return None
    result = value.item() if hasattr(value, "item") else value
    if isinstance(result, (float, np.floating)) and not np.isfinite(result):
        return None
    return result


class DEMReader:
    """Context-managed, read-only Rasterio wrapper for the lunar DEM."""

    def __init__(self, dem_path: str | Path | None = None, band: int = 1):
        self.path = Path(dem_path) if dem_path is not None else default_dem_path()
        self.band = int(band)
        self._dataset = None

    def __enter__(self) -> "DEMReader":
        if not self.path.is_file():
            raise FileNotFoundError(f"LOLA DEM not found: {self.path}")
        self._dataset = rasterio.open(self.path, "r")
        if not 1 <= self.band <= self._dataset.count:
            self.close()
            raise ValueError(f"Band {self.band} is outside raster band range.")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        if self._dataset is not None:
            self._dataset.close()
            self._dataset = None

    @property
    def dataset(self):
        if self._dataset is None:
            raise RuntimeError("DEMReader must be used inside a with block.")
        return self._dataset

    def metadata(self) -> dict[str, Any]:
        """Return JSON-ready raster metadata; no raster objects are exposed."""
        ds = self.dataset
        return {
            "path": str(self.path),
            "exists": True,
            "driver": str(ds.driver),
            "width_px": int(ds.width),
            "height_px": int(ds.height),
            "band_count": int(ds.count),
            "crs": ds.crs.to_string() if ds.crs else None,
            "transform": [float(v) for v in tuple(ds.transform)[:6]],
            "resolution_m": [abs(float(ds.transform.a)), abs(float(ds.transform.e))],
            "bounds_m": {
                "left_m": float(ds.bounds.left), "bottom_m": float(ds.bounds.bottom),
                "right_m": float(ds.bounds.right), "top_m": float(ds.bounds.top),
            },
            "nodata": _json_number(ds.nodata),
            "dtype": str(ds.dtypes[self.band - 1]),
            "moon_radius_m": MOON_RADIUS_M,
            "expected_proj4": PROJ4_SOUTH_POLAR,
        }

    def pixel_for_xy(self, x_m: float, y_m: float) -> tuple[int, int] | None:
        """Return (row, col) if projected coordinate maps to a raster pixel."""
        ds = self.dataset
        col, row = rowcol(ds.transform, x_m, y_m)
        row, col = int(row), int(col)
        if 0 <= row < ds.height and 0 <= col < ds.width:
            return row, col
        return None

    def read_pixel(self, row: int, col: int) -> float | None:
        """Read one pixel, returning None for masked/NoData/non-finite values."""
        ds = self.dataset
        if not (0 <= row < ds.height and 0 <= col < ds.width):
            return None
        value = ds.read(self.band, window=((row, row + 1), (col, col + 1)), masked=True)[0, 0]
        if np.ma.is_masked(value):
            return None
        number = float(value)
        return number if np.isfinite(number) else None


def inspect_dem(dem_path: str | Path | None = None) -> dict[str, Any]:
    """Inspect the expected DEM without raising when the file is absent."""
    path = Path(dem_path) if dem_path is not None else default_dem_path()
    if not path.is_file():
        return {"path": str(path), "exists": False, "status": "dem_unavailable"}
    with DEMReader(path) as reader:
        result = reader.metadata()
    result["status"] = "ok"
    return result


def site_coverage(
    lat_deg: float, lon_deg: float, dem_path: str | Path | None = None
) -> dict[str, Any]:
    """Check nominal envelope, actual raster bounds and pixel validity."""
    lat, lon = normalize_latlon(lat_deg, lon_deg)
    x_m, y_m = latlon_to_xy(lat, lon)
    base = {
        "lat_deg": lat, "lon_deg": lon, "x_m": x_m, "y_m": y_m,
        "nominal_coverage": is_nominal_dem_latitude(lat),
        "raster_coverage": False, "pixel_covered": False, "status": "",
        "row": None, "col": None,
    }
    if not base["nominal_coverage"]:
        base["status"] = "outside_nominal_coverage"
        return base
    path = Path(dem_path) if dem_path is not None else default_dem_path()
    if not path.is_file():
        base["status"] = "dem_unavailable"
        return base
    with DEMReader(path) as reader:
        ds = reader.dataset
        if not (ds.bounds.left <= x_m < ds.bounds.right and
                ds.bounds.bottom < y_m <= ds.bounds.top):
            base["status"] = "outside_raster_bounds"
            return base
        pixel = reader.pixel_for_xy(x_m, y_m)
        if pixel is None:
            base["status"] = "outside_raster_bounds"
            return base
        row, col = pixel
        base.update({"raster_coverage": True, "row": row, "col": col})
        valid = reader.read_pixel(row, col) is not None
        base["pixel_covered"] = valid
        base["status"] = "covered" if valid else "nodata"
    return base


def sample_elevation(
    lat_deg: float, lon_deg: float, dem_path: str | Path | None = None
) -> dict[str, Any]:
    """Sample local DEM elevation in metres above the reference sphere."""
    coverage = site_coverage(lat_deg, lon_deg, dem_path)
    result = {
        "lat_deg": coverage["lat_deg"], "lon_deg": coverage["lon_deg"],
        "elevation_m": None, "status": coverage["status"],
        "x_m": coverage["x_m"], "y_m": coverage["y_m"],
    }
    if not coverage["pixel_covered"]:
        return result
    path = Path(dem_path) if dem_path is not None else default_dem_path()
    with DEMReader(path) as reader:
        result["elevation_m"] = reader.read_pixel(coverage["row"], coverage["col"])
    result["status"] = "ok" if result["elevation_m"] is not None else "nodata"
    return result
