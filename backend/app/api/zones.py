"""Provisional API routes for Layer 3: Landing-Zone Identification & Evaluation.

Endpoints:
- GET /api/regions/{region_id}/zones
- POST /api/zones/compare
"""

from fastapi import APIRouter, Depends, status

from app.integrations.frontend_adapter import FrontendAdapter, get_frontend_adapter
from app.models.zone import (
    ZoneComparisonRequest,
    ZoneComparisonResponse,
    ZoneListResponse,
)
from app.services.decision_service import DecisionService
from app.services.terrain_service import TerrainService

router = APIRouter(tags=["Layer 3 — Landing Zones"])


def get_terrain_service() -> TerrainService:
    """Dependency provider for TerrainService."""
    return TerrainService()


def get_decision_service() -> DecisionService:
    """Dependency provider for DecisionService."""
    return DecisionService()


@router.get(
    "/regions/{region_id}/zones",
    response_model=ZoneListResponse,
    status_code=status.HTTP_200_OK,
    summary="List candidate landing zones within a Lunar South Pole region",
)
def list_zones_for_region(
    region_id: str,
    terrain_service: TerrainService = Depends(get_terrain_service),
    frontend: FrontendAdapter = Depends(get_frontend_adapter),
) -> ZoneListResponse:
    """Return candidate landing-zone polygons and engineering parameters for `region_id`."""
    result = terrain_service.get_zones_for_region(region_id)
    return frontend.to_response_payload(result)  # type: ignore[return-value]


@router.post(
    "/zones/compare",
    response_model=ZoneComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare and rank exactly three candidate landing zones",
)
def compare_zones(
    payload: ZoneComparisonRequest,
    decision_service: DecisionService = Depends(get_decision_service),
    frontend: FrontendAdapter = Depends(get_frontend_adapter),
) -> ZoneComparisonResponse:
    """Evaluate and rank three user-selected candidate landing zones and recommend the winner."""
    result = decision_service.compare_three_zones(payload)
    return frontend.to_response_payload(result)  # type: ignore[return-value]
