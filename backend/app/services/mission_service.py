"""Mission Service for Layer 1: Mission Configuration & Earth-Moon Interception.

Manages mission configurations in an in-memory store (intentionally avoiding database
overhead for the 48-hour hackathon foundation) and coordinates with `AstronomyService`.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from app.core.exceptions import ResourceNotFoundError
from app.models.common import DataOrigin
from app.models.mission import MissionConfigureRequest, MissionResponse
from app.services.astronomy_service import AstronomyService

logger = logging.getLogger("luna_nav.services.mission")

# In-memory store for configured missions during the backend session
_MISSION_STORE: Dict[str, MissionResponse] = {}
DEFAULT_MOCK_MISSION_ID = "msn-default-mock"


class MissionService:
    """Business logic for configuring and retrieving lunar missions (Layer 1)."""

    def __init__(self, astronomy_service: Optional[AstronomyService] = None) -> None:
        self.astronomy_service = astronomy_service or AstronomyService()
        self._ensure_default_mission_seeded()

    def _ensure_default_mission_seeded(self) -> None:
        """Seed a deterministic default mock mission so downstream layers/reports work immediately."""
        if DEFAULT_MOCK_MISSION_ID not in _MISSION_STORE:
            default_arrival = datetime(2027, 6, 15, 14, 0, 0, tzinfo=timezone.utc)
            window, orbital_params, waypoints = self.astronomy_service.compute_interception(
                default_arrival
            )
            _MISSION_STORE[DEFAULT_MOCK_MISSION_ID] = MissionResponse(
                mission_id=DEFAULT_MOCK_MISSION_ID,
                mission_name="LUNA-NAV-DEFAULT-SIMULATION",
                status="CONFIGURED_SIMULATED",
                data_origin=DataOrigin.SIMULATED,
                created_at_utc=datetime(2026, 11, 13, 0, 0, 0, tzinfo=timezone.utc),
                interception_window=window,
                orbital_parameters=orbital_params,
                trajectory_waypoints=waypoints,
                notes="Pre-seeded MOCK mission configuration for independent testing.",
            )

    def configure_mission(self, request: MissionConfigureRequest) -> MissionResponse:
        """Create and store a new mission configuration from user arrival-date input."""
        mission_id = f"msn-{uuid.uuid4().hex[:8]}"
        logger.info(
            "Configuring mission '%s' (%s) for arrival=%s",
            request.mission_name,
            mission_id,
            request.target_arrival_utc.isoformat(),
        )

        window, orbital_params, waypoints = self.astronomy_service.compute_interception(
            request.target_arrival_utc
        )

        mission = MissionResponse(
            mission_id=mission_id,
            mission_name=request.mission_name,
            status="CONFIGURED_SIMULATED",
            data_origin=DataOrigin.SIMULATED,
            created_at_utc=datetime.now(timezone.utc),
            interception_window=window,
            orbital_parameters=orbital_params,
            trajectory_waypoints=waypoints,
            notes=request.notes,
        )
        _MISSION_STORE[mission_id] = mission
        return mission

    def get_mission(self, mission_id: str) -> MissionResponse:
        """Retrieve a previously configured mission by `mission_id`."""
        mission = _MISSION_STORE.get(mission_id)
        if not mission:
            raise ResourceNotFoundError(resource_type="Mission", resource_id=mission_id)
        return mission
