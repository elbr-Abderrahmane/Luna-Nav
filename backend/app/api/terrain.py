"""Terrain & GIS REST Endpoints (`/api/terrain/*`).

Exposes P2's Lunar Coordinate & LOLA DEM utilities (`lunanav.coords` and `lunanav.terrain`):
- `GET /api/terrain/inspect`   — LOLA DEM raster metadata & availability status
- `GET /api/terrain/coverage`  — Check whether (lat_deg, lon_deg) is inside nominal 80–90°S & raster coverage
- `GET /api/terrain/elevation` — Sample local DEM elevation (m above 1737.4 km reference sphere)
- `GET /api/terrain/heightmap` — Extract a clipped local square heightmap (JSON-safe nulls for NoData)
- `GET /api/terrain/metrics`   — Compute local 3x3 Horn slope (deg), roughness (m), and elevation stats
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse

from lunanav.terrain import (
    extract_heightmap,
    inspect_dem,
    local_roughness,
    local_slope,
    sample_elevation,
    site_coverage,
    terrain_summary,
)

router = APIRouter(prefix="/terrain", tags=["Terrain & Lunar Coordinates (P2)"])


def _bad_coord_response(exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"status": "error", "error": {"code": "INVALID_COORDINATES", "message": str(exc)}},
    )


@router.get(
    "/inspect",
    summary="Inspect NASA LOLA south-pole DEM availability and GeoTIFF metadata",
)
def get_dem_inspection() -> Any:
    return inspect_dem()


@router.get(
    "/coverage",
    summary="Check whether lunar coordinates lie within nominal (80–90°S) and actual LOLA DEM coverage",
)
def get_terrain_coverage(
    lat_deg: float = Query(..., description="Planetocentric latitude in degrees (-90..90)"),
    lon_deg: float = Query(..., description="East-positive longitude in degrees (-180..180)"),
) -> Any:
    try:
        return site_coverage(lat_deg, lon_deg)
    except ValueError as exc:
        return _bad_coord_response(exc)


@router.get(
    "/elevation",
    summary="Sample local elevation in metres above the 1737.4 km reference sphere",
)
def get_terrain_elevation(
    lat_deg: float = Query(..., description="Planetocentric latitude in degrees (-90..90)"),
    lon_deg: float = Query(..., description="East-positive longitude in degrees (-180..180)"),
) -> Any:
    try:
        return sample_elevation(lat_deg, lon_deg)
    except ValueError as exc:
        return _bad_coord_response(exc)


@router.get(
    "/heightmap",
    summary="Extract a local square DEM heightmap window around (lat_deg, lon_deg)",
)
def get_terrain_heightmap(
    lat_deg: float = Query(..., description="Planetocentric latitude in degrees (-90..90)"),
    lon_deg: float = Query(..., description="East-positive longitude in degrees (-180..180)"),
    radius_m: float = Query(default=1600.0, gt=0, le=50000, description="Window half-width in metres"),
) -> Any:
    try:
        return extract_heightmap(lat_deg, lon_deg, radius_m=radius_m)
    except ValueError as exc:
        return _bad_coord_response(exc)


@router.get(
    "/metrics",
    summary="Compute local descriptive terrain metrics (slope, roughness, min/max/mean elevation)",
)
def get_terrain_metrics(
    lat_deg: float = Query(..., description="Planetocentric latitude in degrees (-90..90)"),
    lon_deg: float = Query(..., description="East-positive longitude in degrees (-180..180)"),
    radius_m: float = Query(default=240.0, gt=0, le=10000, description="Local window radius in metres"),
) -> Any:
    try:
        cov = site_coverage(lat_deg, lon_deg)
        slope = local_slope(lat_deg, lon_deg)
        rough = local_roughness(lat_deg, lon_deg, radius_m=radius_m)
        summary = terrain_summary(lat_deg, lon_deg, radius_m=radius_m)
        return {
            "status": summary["status"],
            "lat_deg": cov["lat_deg"],
            "lon_deg": cov["lon_deg"],
            "coverage": cov,
            "slope_deg": slope["slope_deg"],
            "slope_status": slope["status"],
            "roughness_m": rough["roughness_m"],
            "summary": summary,
        }
    except ValueError as exc:
        return _bad_coord_response(exc)

