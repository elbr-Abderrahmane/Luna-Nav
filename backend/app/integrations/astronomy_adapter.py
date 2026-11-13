"""Provisional Integration Adapter for Person 3 (Astronomy & Orbital Mechanics).

PROVISIONAL INTERFACE — Awaiting Person 3's Technical Specification README.
IMPORTANT RESTRICTION: This adapter does NOT implement real orbital mechanics,
ephemeris calculations, solar illumination raytracing, or Earth visibility geometry.
All outputs in `MockAstronomyAdapter` are static structural placeholders explicitly
marked as SIMULATED.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Tuple

from app.core.config import settings
from app.core.exceptions import AdapterIntegrationError
from app.models.common import LunarCoordinates, Measurement, MeasurementStatus
from app.models.mission import (
    InterceptionWindow,
    OrbitalParametersSummary,
    TrajectoryWaypoint3D,
)

logger = logging.getLogger("luna_nav.integrations.astronomy")


class BaseAstronomyAdapter(ABC):
    """PROVISIONAL INTERFACE for Person 3's Astronomy & Orbital Mechanics module.

    Covers:
    1. Mission calculations (interception window, transfer trajectory, orbital summary).
    2. Illumination analysis (solar lighting conditions at lunar coordinates).
    3. Earth visibility (direct-to-Earth communication geometry).
    """

    @abstractmethod
    def calculate_mission_interception(
        self, target_arrival_utc: datetime
    ) -> Tuple[InterceptionWindow, OrbitalParametersSummary, List[TrajectoryWaypoint3D]]:
        """Return interception window, orbital parameters, and 3D transfer waypoints for an arrival date."""

    @abstractmethod
    def analyze_illumination(
        self, coordinates: LunarCoordinates, target_arrival_utc: datetime
    ) -> Measurement:
        """Return solar illumination estimate for given coordinates and mission epoch."""

    @abstractmethod
    def analyze_earth_visibility(
        self, coordinates: LunarCoordinates, target_arrival_utc: datetime
    ) -> Measurement:
        """Return direct-to-Earth visibility estimate for given coordinates and mission epoch."""


class MockAstronomyAdapter(BaseAstronomyAdapter):
    """Mock implementation returning static, clearly labeled SIMULATED structural data."""

    def calculate_mission_interception(
        self, target_arrival_utc: datetime
    ) -> Tuple[InterceptionWindow, OrbitalParametersSummary, List[TrajectoryWaypoint3D]]:
        logger.debug(
            "MockAstronomyAdapter: generating simulated mission interception for arrival=%s",
            target_arrival_utc.isoformat(),
        )
        # Fixed structural offsets (NOT orbital mechanics; purely structural placeholder for UI/API testing)
        simulated_transfer_hours = 76.0
        estimated_launch = target_arrival_utc - timedelta(hours=simulated_transfer_hours)
        window_start = estimated_launch - timedelta(hours=2)
        window_end = estimated_launch + timedelta(hours=2)

        window = InterceptionWindow(
            window_start_utc=window_start,
            window_end_utc=window_end,
            estimated_launch_utc=estimated_launch,
            confirmed_arrival_utc=target_arrival_utc,
        )

        orbital_params = OrbitalParametersSummary(
            earth_moon_distance=Measurement(
                value=384400.0,
                unit="km",
                status=MeasurementStatus.SIMULATED,
                note="SIMULATED nominal placeholder distance; awaiting Person 3 ephemeris module.",
            ),
            estimated_transfer_duration=Measurement(
                value=simulated_transfer_hours,
                unit="hours",
                status=MeasurementStatus.SIMULATED,
                note="SIMULATED placeholder transfer duration; awaiting Person 3 trajectory solver.",
            ),
            solar_sub_longitude=Measurement(
                value=None,
                unit="deg",
                status=MeasurementStatus.UNAVAILABLE,
                note="UNAVAILABLE: Ephemeris sub-solar longitude awaiting Person 3 module (kept null, not 0).",
            ),
            earth_sub_latitude=Measurement(
                value=-6.5,
                unit="deg",
                status=MeasurementStatus.SIMULATED,
                note="SIMULATED placeholder libration latitude; awaiting Person 3 module.",
            ),
            coordinate_frame_provisional="PROVISIONAL_EARTH_CENTERED_INERTIAL_MOCK",
        )

        # 4 structural 3D curve points between Earth origin and simulated lunar position
        waypoints = [
            TrajectoryWaypoint3D(
                step_index=0,
                timestamp_utc=estimated_launch,
                position_km=[6578.0, 0.0, 0.0],
            ),
            TrajectoryWaypoint3D(
                step_index=1,
                timestamp_utc=estimated_launch + timedelta(hours=25),
                position_km=[128000.0, 42000.0, -3500.0],
            ),
            TrajectoryWaypoint3D(
                step_index=2,
                timestamp_utc=estimated_launch + timedelta(hours=50),
                position_km=[265000.0, 68000.0, -7200.0],
            ),
            TrajectoryWaypoint3D(
                step_index=3,
                timestamp_utc=target_arrival_utc,
                position_km=[378000.0, 69500.0, -11200.0],
            ),
        ]

        return window, orbital_params, waypoints

    def analyze_illumination(
        self, coordinates: LunarCoordinates, target_arrival_utc: datetime
    ) -> Measurement:
        return Measurement(
            value=84.0,
            unit="%",
            status=MeasurementStatus.SIMULATED,
            note=(
                f"SIMULATED static illumination placeholder for ({coordinates.latitude}, "
                f"{coordinates.longitude}) at {target_arrival_utc.isoformat()}; awaiting Person 3."
            ),
        )

    def analyze_earth_visibility(
        self, coordinates: LunarCoordinates, target_arrival_utc: datetime
    ) -> Measurement:
        return Measurement(
            value=79.5,
            unit="%",
            status=MeasurementStatus.SIMULATED,
            note=(
                f"SIMULATED static Earth visibility placeholder for ({coordinates.latitude}, "
                f"{coordinates.longitude}) at {target_arrival_utc.isoformat()}; awaiting Person 3."
            ),
        )


class RealAstronomyAdapterStub(BaseAstronomyAdapter):
    """Placeholder for Person 3's real Astronomy & Orbital Mechanics module."""

    def _not_connected(self, operation: str) -> None:
        raise AdapterIntegrationError(
            adapter_name="RealAstronomyAdapterStub (Person 3 - Astronomy & Orbital Mechanics)",
            message=(
                f"Operation '{operation}' called with USE_MOCK_ASTRONOMY=false, "
                "but Person 3's Astronomy module has not been wired yet."
            ),
        )

    def calculate_mission_interception(
        self, target_arrival_utc: datetime
    ) -> Tuple[InterceptionWindow, OrbitalParametersSummary, List[TrajectoryWaypoint3D]]:
        self._not_connected("calculate_mission_interception")
        raise AssertionError("Unreachable")

    def analyze_illumination(
        self, coordinates: LunarCoordinates, target_arrival_utc: datetime
    ) -> Measurement:
        self._not_connected("analyze_illumination")
        raise AssertionError("Unreachable")

    def analyze_earth_visibility(
        self, coordinates: LunarCoordinates, target_arrival_utc: datetime
    ) -> Measurement:
        self._not_connected("analyze_earth_visibility")
        raise AssertionError("Unreachable")


def get_astronomy_adapter() -> BaseAstronomyAdapter:
    """Factory returning either MockAstronomyAdapter or RealAstronomyAdapterStub."""
    if settings.use_mock_astronomy:
        return MockAstronomyAdapter()
    return RealAstronomyAdapterStub()
