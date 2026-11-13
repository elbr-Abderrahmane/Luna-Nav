"""Provisional API routes for Layer 4: Optimal Landing-Point Identification & Evaluation.

Endpoints:
- GET /api/zones/{zone_id}/points
- POST /api/points/evaluate
"""

from fastapi import APIRouter, Depends, status

from app.integrations.frontend_adapter import FrontendAdapter, get_frontend_adapter
from app.models.point import (
    PointEvaluateRequest,
    PointEvaluationResponse,
    PointListResponse,
)
from app.services.decision_service import DecisionService
from app.services.terrain_service import TerrainService

router = APIRouter(tags=["Layer 4 — Landing Points"])


def get_terrain_service() -> TerrainService:
    """Dependency provider for TerrainService."""
    return TerrainService()


def get_decision_service() -> DecisionService:
    """Dependency provider for DecisionService."""
    return DecisionService()


@router.get(
    "/zones/{zone_id}/points",
    response_model=PointListResponse,
    status_code=status.HTTP_200_OK,
    summary="List candidate landing points inside a landing zone",
)
def list_points_for_zone(
    zone_id: str,
    terrain_service: TerrainService = Depends(get_terrain_service),
    frontend: FrontendAdapter = Depends(get_frontend_adapter),
) -> PointListResponse:
    """Return candidate touchdown markers and local engineering parameters for `zone_id`."""
    result = terrain_service.get_points_for_zone(zone_id)
    return frontend.to_response_payload(result)  # type: ignore[return-value]


@router.post(
    "/points/evaluate",
    response_model=PointEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate candidate landing points and identify optimal touchdown coordinates",
)
def evaluate_points(
    payload: PointEvaluateRequest,
    decision_service: DecisionService = Depends(get_decision_service),
    frontend: FrontendAdapter = Depends(get_frontend_adapter),
) -> PointEvaluationResponse:
    """Rank candidate landing points in a zone and return the recommended touchdown coordinates."""
    result = decision_service.evaluate_points(payload)
    return frontend.to_response_payload(result)  # type: ignore[return-value]
