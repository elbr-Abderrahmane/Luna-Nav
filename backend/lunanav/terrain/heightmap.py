"""JSON-ready extraction of local DEM heightmaps."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from rasterio.transform import xy
from rasterio.windows import Window

from lunanav.coords import latlon_to_xy, normalize_latlon
from lunanav.terrain.dem import DEMReader, site_coverage


def extract_heightmap(
    lat_deg: float,
    lon_deg: float,
    radius_m: float,
    dem_path: str | Path | None = None,
) -> dict[str, Any]:
    """Extract a clipped square heightmap around a lunar coordinate.

    NoData and out-of-raster cells are returned as JSON nulls.
    """
    radius = float(radius_m)

    if not np.isfinite(radius) or radius <= 0:
        raise ValueError("radius_m must be a finite positive number.")

    lat, lon = normalize_latlon(lat_deg, lon_deg)
    coverage = site_coverage(lat, lon, dem_path)

    if not coverage["raster_coverage"]:
        return {
            "status": coverage["status"],
            "lat_deg": lat,
            "lon_deg": lon,
            "radius_m": radius,
            "rows": 0,
            "cols": 0,
            "values_m": [],
        }

    path = Path(dem_path) if dem_path is not None else None

    with DEMReader(path) as reader:
        ds = reader.dataset

        x_m, y_m = latlon_to_xy(lat, lon)
        center = reader.pixel_for_xy(x_m, y_m)

        if center is None:
            return {
                "status": "outside_raster_bounds",
                "lat_deg": lat,
                "lon_deg": lon,
                "radius_m": radius,
                "rows": 0,
                "cols": 0,
                "values_m": [],
            }

        row, col = center

        res_x = abs(float(ds.transform.a))
        res_y = abs(float(ds.transform.e))

        half_cols = max(1, int(np.ceil(radius / res_x)))
        half_rows = max(1, int(np.ceil(radius / res_y)))

        row0 = max(0, row - half_rows)
        row1 = min(ds.height, row + half_rows + 1)

        col0 = max(0, col - half_cols)
        col1 = min(ds.width, col + half_cols + 1)

        if row0 >= row1 or col0 >= col1:
            return {
                "status": "empty_window",
                "lat_deg": lat,
                "lon_deg": lon,
                "radius_m": radius,
                "rows": 0,
                "cols": 0,
                "values_m": [],
            }

        data = ds.read(
            1,
            window=Window(
                col0,
                row0,
                col1 - col0,
                row1 - row0,
            ),
            masked=True,
        )

        values = []

        for row_values in data:
            values.append([
                None
                if np.ma.is_masked(v) or not np.isfinite(float(v))
                else float(v)
                for v in row_values
            ])

        # Calculate raster window boundaries without deprecated
        # Affine multiplication using the * operator.
        left_m, top_m = xy(
            ds.transform,
            row0,
            col0,
            offset="ul",
        )

        right_m, bottom_m = xy(
            ds.transform,
            row1,
            col1,
            offset="ul",
        )

        return {
            "status": "ok",
            "lat_deg": lat,
            "lon_deg": lon,
            "radius_m": radius,
            "rows": int(data.shape[0]),
            "cols": int(data.shape[1]),
            "resolution_m": {
                "x_m": res_x,
                "y_m": res_y,
            },
            "center_pixel": {
                "row": row,
                "col": col,
            },
            "window_pixel_bounds": {
                "row_start": row0,
                "row_stop": row1,
                "col_start": col0,
                "col_stop": col1,
            },
            "bounds_m": {
                "left_m": float(left_m),
                "top_m": float(top_m),
                "right_m": float(right_m),
                "bottom_m": float(bottom_m),
            },
            "values_m": values,
            "nodata_count": int(
                sum(
                    v is None
                    for line in values
                    for v in line
                )
            ),
        }
