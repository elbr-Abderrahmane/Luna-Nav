"""Terrain Service for LUNA NAV.

Coordinates geographical regions, landing-zone polygons, and candidate landing points
through `BaseTerrainAdapter` (Person 2's GIS & Terrain Analysis boundary).
"""

import logging
from typing import List, Optional

from app.core.exceptions import ResourceNotFoundError
from app.integrations.terrain_adapter import BaseTerrainAdapter, get_terrain_adapter
from app.models.point import LandingPointModel, PointListResponse
from app.models.region import RegionModel
from app.models.zone import LandingZoneModel, ZoneListResponse

logger = logging.getLogger("luna_nav.services.terrain")


class TerrainService:
    """Service layer managing terrain queries for regions, zones, and landing points."""

    def __init__(self, adapter: Optional[BaseTerrainAdapter] = None) -> None:
        self.adapter = adapter or get_terrain_adapter()

    def get_all_regions(self) -> List[RegionModel]:
        """Return all predefined Lunar South Pole exploration regions."""
        return self.adapter.fetch_south_pole_regions()

    def get_region_by_id(self, region_id: str) -> RegionModel:
        """Return a specific Lunar South Pole region or raise ResourceNotFoundError."""
        region = self.adapter.fetch_region_terrain(region_id)
        if not region:
            raise ResourceNotFoundError(resource_type="Region", resource_id=region_id)
        return region

    def get_zones_for_region(self, region_id: str) -> ZoneListResponse:
        """Verify region exists and return candidate landing zones within that region."""
        self.get_region_by_id(region_id)
        zones = self.adapter.identify_landing_zones(region_id)
        return ZoneListResponse(
            region_id=region_id,
            count=len(zones),
            zones=zones,
        )

    def get_zone_by_id(self, zone_id: str) -> LandingZoneModel:
        """Retrieve a single landing zone by ID or raise ResourceNotFoundError."""
        zone = self.adapter.fetch_zone_terrain(zone_id)
        if not zone:
            raise ResourceNotFoundError(resource_type="LandingZone", resource_id=zone_id)
        return zone

    def get_points_for_zone(self, zone_id: str) -> PointListResponse:
        """Verify zone exists and return candidate landing points inside that zone."""
        self.get_zone_by_id(zone_id)
        points = self.adapter.identify_landing_points(zone_id)
        recommended_id: Optional[str] = None
        for pt in points:
            if pt.is_provisional_optimal:
                recommended_id = pt.point_id
                break
        if recommended_id is None and points:
            recommended_id = points[0].point_id

        return PointListResponse(
            zone_id=zone_id,
            count=len(points),
            recommended_point_id=recommended_id,
            points=points,
        )
