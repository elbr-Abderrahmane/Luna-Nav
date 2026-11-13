"""Astronomy Service for LUNA NAV.

Coordinates astronomical and orbital mechanics requests through `BaseAstronomyAdapter`
(Person 3's integration boundary).
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from app.integrations.astronomy_adapter import BaseAstronomyAdapter, get_astronomy_adapter
from app.models.common import LunarCoordinates, Measurement
from app.models.mission import (
    InterceptionWindow,
    OrbitalParametersSummary,
    TrajectoryWaypoint3D,
)

logger = logging.getLogger("luna_nav.services.astronomy")


class AstronomyService:
    """Service layer mediating between business workflows and Person 3's AstronomyAdapter."""

    def __init__(self, adapter: Optional[BaseAstronomyAdapter] = None) -> None:
        self.adapter = adapter or get_astronomy_adapter()

    def compute_interception(
        self, target_arrival_utc: datetime
    ) -> Tuple[InterceptionWindow, OrbitalParametersSummary, List[TrajectoryWaypoint3D]]:
        """Delegate Earth-Moon interception calculation to the configured AstronomyAdapter."""
        logger.info(
            "Computing mission interception via %s for target_arrival_utc=%s",
            type(self.adapter).__name__,
            target_arrival_utc.isoformat(),
        )
        return self.adapter.calculate_mission_interception(target_arrival_utc)

    def get_illumination(
        self, coordinates: LunarCoordinates, target_arrival_utc: datetime
    ) -> Measurement:
        """Retrieve simulated or module-computed solar illumination for coordinates."""
        return self.adapter.analyze_illumination(coordinates, target_arrival_utc)

    def get_earth_visibility(
        self, coordinates: LunarCoordinates, target_arrival_utc: datetime
    ) -> Measurement:
        """Retrieve simulated or module-computed direct-to-Earth visibility for coordinates."""
        return self.adapter.analyze_earth_visibility(coordinates, target_arrival_utc)
