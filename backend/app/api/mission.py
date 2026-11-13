"""Provisional API routes for Layer 1: Mission Configuration & Earth-Moon Interception.

Endpoints:
- POST /api/mission/configure
- GET /api/mission/{mission_id}
"""

from fastapi import APIRouter, Depends, status

from app.integrations.frontend_adapter import FrontendAdapter, get_frontend_adapter
from app.models.mission import MissionConfigureRequest, MissionResponse
from app.services.mission_service import MissionService

router = APIRouter(prefix="/mission", tags=["Layer 1 — Mission Configuration"])


def get_mission_service() -> MissionService:
    """Dependency provider for MissionService."""
    return MissionService()


@router.post(
    "/configure",
    response_model=MissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Configure mission arrival date and compute simulated Earth-Moon interception",
)
def configure_mission(
    payload: MissionConfigureRequest,
    service: MissionService = Depends(get_mission_service),
    frontend: FrontendAdapter = Depends(get_frontend_adapter),
) -> MissionResponse:
    """Configure a lunar mission and return simulated interception window & 3D trajectory."""
    result = service.configure_mission(payload)
    return frontend.to_response_payload(result)  # type: ignore[return-value]


@router.get(
    "/{mission_id}",
    response_model=MissionResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a configured mission by ID",
)
def get_mission(
    mission_id: str,
    service: MissionService = Depends(get_mission_service),
    frontend: FrontendAdapter = Depends(get_frontend_adapter),
) -> MissionResponse:
    """Retrieve mission configuration and Earth-Moon interception parameters."""
    result = service.get_mission(mission_id)
    return frontend.to_response_payload(result)  # type: ignore[return-value]
