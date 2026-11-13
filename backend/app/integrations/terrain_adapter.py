"""Provisional Integration Adapter for Person 2 (Terrain Analysis & GIS).

PROVISIONAL INTERFACE — Awaiting Person 2's Technical Specification README.
Do not assume final function signatures or LOLA/LRO raster schemas here.
When Person 2 delivers their GIS package, implement `RealTerrainAdapter` below
and set `USE_MOCK_TERRAIN=false` in `.env`.
"""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from app.core.config import settings
from app.core.exceptions import AdapterIntegrationError
from app.models.point import LandingPointModel
from app.models.region import RegionModel
from app.models.zone import LandingZoneModel

logger = logging.getLogger("luna_nav.integrations.terrain")


class BaseTerrainAdapter(ABC):
    """PROVISIONAL INTERFACE for Person 2's Terrain Analysis & GIS module.

    Covers:
    1. Regional terrain analysis (Lunar South Pole sectors).
    2. Landing-zone identification (candidate polygons & terrain parameters).
    3. Landing-point identification (candidate markers & local terrain metrics).
    """

    @abstractmethod
    def fetch_south_pole_regions(self) -> List[RegionModel]:
        """Return candidate Lunar South Pole regions with preliminary terrain summaries."""

    @abstractmethod
    def fetch_region_terrain(self, region_id: str) -> Optional[RegionModel]:
        """Return regional terrain analysis for a specific `region_id`."""

    @abstractmethod
    def identify_landing_zones(self, region_id: str) -> List[LandingZoneModel]:
        """Identify candidate landing-zone polygons and terrain metrics within `region_id`."""

    @abstractmethod
    def fetch_zone_terrain(self, zone_id: str) -> Optional[LandingZoneModel]:
        """Return terrain metrics and polygon geometry for a single `zone_id`."""

    @abstractmethod
    def identify_landing_points(self, zone_id: str) -> List[LandingPointModel]:
        """Identify candidate touchdown points within a landing zone."""


class MockTerrainAdapter(BaseTerrainAdapter):
    """Mock implementation reading structural GeoJSON/JSON fixtures from `app/mock_data/`."""

    def __init__(self, mock_data_dir: Optional[Path] = None) -> None:
        self.mock_data_dir = mock_data_dir or settings.mock_data_dir

    def _load_json(self, filename: str) -> dict:
        filepath = self.mock_data_dir / filename
        if not filepath.exists():
            raise AdapterIntegrationError(
                adapter_name="MockTerrainAdapter",
                message=f"Mock dataset file not found: {filepath}",
            )
        with filepath.open("r", encoding="utf-8") as f:
            return json.load(f)

    def fetch_south_pole_regions(self) -> List[RegionModel]:
        logger.debug("MockTerrainAdapter: loading regions from regions.json")
        payload = self._load_json("regions.json")
        return [RegionModel.model_validate(item) for item in payload.get("regions", [])]

    def fetch_region_terrain(self, region_id: str) -> Optional[RegionModel]:
        for region in self.fetch_south_pole_regions():
            if region.region_id == region_id:
                return region
        return None

    def identify_landing_zones(self, region_id: str) -> List[LandingZoneModel]:
        logger.debug("MockTerrainAdapter: loading zones for region_id=%s", region_id)
        payload = self._load_json("zones.json")
        zones = [
            LandingZoneModel.model_validate(item)
            for item in payload.get("zones", [])
            if item.get("region_id") == region_id
        ]
        return zones

    def fetch_zone_terrain(self, zone_id: str) -> Optional[LandingZoneModel]:
        payload = self._load_json("zones.json")
        for item in payload.get("zones", []):
            if item.get("zone_id") == zone_id:
                return LandingZoneModel.model_validate(item)
        return None

    def identify_landing_points(self, zone_id: str) -> List[LandingPointModel]:
        logger.debug("MockTerrainAdapter: loading points for zone_id=%s", zone_id)
        payload = self._load_json("points.json")
        points = [
            LandingPointModel.model_validate(item)
            for item in payload.get("points", [])
            if item.get("zone_id") == zone_id
        ]
        return points


class RealTerrainAdapterStub(BaseTerrainAdapter):
    """Placeholder for Person 2's real GIS & Terrain module integration."""

    def _not_connected(self, operation: str) -> None:
        raise AdapterIntegrationError(
            adapter_name="RealTerrainAdapterStub (Person 2 - Terrain & GIS)",
            message=(
                f"Operation '{operation}' called with USE_MOCK_TERRAIN=false, "
                "but Person 2's Terrain Analysis module has not been wired yet."
            ),
        )

    def fetch_south_pole_regions(self) -> List[RegionModel]:
        self._not_connected("fetch_south_pole_regions")
        return []

    def fetch_region_terrain(self, region_id: str) -> Optional[RegionModel]:
        self._not_connected("fetch_region_terrain")
        return None

    def identify_landing_zones(self, region_id: str) -> List[LandingZoneModel]:
        self._not_connected("identify_landing_zones")
        return []

    def fetch_zone_terrain(self, zone_id: str) -> Optional[LandingZoneModel]:
        self._not_connected("fetch_zone_terrain")
        return None

    def identify_landing_points(self, zone_id: str) -> List[LandingPointModel]:
        self._not_connected("identify_landing_points")
        return []


def get_terrain_adapter() -> BaseTerrainAdapter:
    """Factory returning either MockTerrainAdapter or RealTerrainAdapterStub based on settings."""
    if settings.use_mock_terrain:
        return MockTerrainAdapter()
    return RealTerrainAdapterStub()
