"""Region Service for Layer 2: Lunar South Pole Regional Exploration.

Provides dedicated business operations for listing and inspecting South Pole regions,
collaborating with `TerrainService`.
"""

import logging
from typing import Optional

from app.models.region import RegionDetailResponse, RegionListResponse
from app.services.terrain_service import TerrainService

logger = logging.getLogger("luna_nav.services.region")


class RegionService:
    """Business service for Layer 2 regional exploration."""

    def __init__(self, terrain_service: Optional[TerrainService] = None) -> None:
        self.terrain_service = terrain_service or TerrainService()

    def list_regions(self) -> RegionListResponse:
        """Return all available Lunar South Pole regions."""
        regions = self.terrain_service.get_all_regions()
        logger.info("Listed %d Lunar South Pole regions", len(regions))
        return RegionListResponse(count=len(regions), regions=regions)

    def get_region_detail(self, region_id: str) -> RegionDetailResponse:
        """Return detailed metadata and boundary polygon for a single South Pole region."""
        region = self.terrain_service.get_region_by_id(region_id)
        return RegionDetailResponse(
            region=region,
            recommended_camera_altitude_km=45.0,
        )
