"""Curated landing-site catalog + custom coordinates (challenge objective "site selection").

    from lunanav.astro.sites import list_sites, get_site, resolve_site

`sites.json` lives next to this file. Coordinates are planetocentric degrees, longitude
east-positive -180..180. Each site has `coord_quality`: "landed" (published landing coordinate,
rounded), "approximate" (region centre / target area, check the source) or "exact".
"""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

SITES_FILE = Path(__file__).with_name("sites.json")
CATEGORIES = ("reference", "south_pole_candidate", "artemis", "clps", "international", "apollo")


@lru_cache(maxsize=1)
def _catalog() -> dict:
    with SITES_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def list_sites(category: str | None = None) -> list[dict]:
    """All curated sites (copies), optionally filtered by category."""
    sites = [dict(s) for s in _catalog()["sites"]]
    if category is not None:
        sites = [s for s in sites if s["category"] == category]
    return sites


def get_site(site_id: str) -> dict:
    for s in _catalog()["sites"]:
        if s["id"] == site_id:
            return dict(s)
    raise KeyError(f"unknown site id {site_id!r}")


def normalize_latlon(lat, lon) -> tuple[float, float]:
    """Validate and normalise custom coordinates. Raises ValueError."""
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError) as exc:
        raise ValueError("latitude/longitude must be numbers") from exc
    if not (math.isfinite(lat) and math.isfinite(lon)):
        raise ValueError("latitude/longitude must be finite")
    if not -90.0 <= lat <= 90.0:
        raise ValueError(f"latitude {lat} outside -90..90")
    lon = ((lon + 180.0) % 360.0) - 180.0
    return lat, lon


def resolve_site(site) -> dict:
    """Accept a catalog id, a dict with lat_deg/lon_deg (custom site) or a (lat, lon) pair.

    Returns a dict with at least id, name, lat_deg, lon_deg, category, coord_quality.
    Raises KeyError (unknown id) or ValueError (bad coordinates).
    """
    if isinstance(site, str):
        return get_site(site)
    if isinstance(site, dict):
        if "id" in site and "lat_deg" not in site and "latitude" not in site:
            return get_site(site["id"])
        lat = site.get("lat_deg", site.get("latitude"))
        lon = site.get("lon_deg", site.get("longitude"))
        lat, lon = normalize_latlon(lat, lon)
        out = {"id": site.get("id") or f"custom:{lat:.4f},{lon:.4f}",
               "name": site.get("name") or f"Custom site {lat:.3f}, {lon:.3f}",
               "category": "custom", "status": "custom", "coord_quality": "user_input",
               "mission": None, "agency": None, "notes": site.get("notes", "")}
        if site.get("elevation_m") is not None:
            out["elevation_m"] = float(site["elevation_m"])
        out.update(lat_deg=lat, lon_deg=lon)
        return out
    if isinstance(site, (tuple, list)) and len(site) == 2:
        return resolve_site({"lat_deg": site[0], "lon_deg": site[1]})
    raise ValueError("site must be a catalog id, {'lat_deg','lon_deg'} or (lat, lon)")


__all__ = ["CATEGORIES", "get_site", "list_sites", "normalize_latlon", "resolve_site"]
