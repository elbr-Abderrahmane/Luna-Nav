"""Provisional API routes for Layer 2: Lunar South Pole Regional Exploration.

Endpoints:
- GET /api/regions
- GET /api/regions/{region_id}
"""

from fastapi import APIRouter, Depends, status

from app.integrations.frontend_adapter import FrontendAdapter, get_frontend_adapter
from app.models.region import RegionDetailResponse, RegionListResponse
from app.services.region_service import RegionService

router = APIRouter(prefix="/regions", tags=["Layer 2 — Lunar South Pole Regions"])


def get_region_service() -> RegionService:
    """Dependency provider for RegionService."""
    return RegionService()


@router.get(
    "",
    response_model=RegionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List predefined Lunar South Pole exploration regions",
)
def list_regions(
    service: RegionService = Depends(get_region_service),
    frontend: FrontendAdapter = Depends(get_frontend_adapter),
) -> RegionListResponse:
    """Return all predefined Lunar South Pole regions with GeoJSON boundaries and mock metrics."""
    result = service.list_regions()
    return frontend.to_response_payload(result)  # type: ignore[return-value]


@router.get(
    "/{region_id}",
    response_model=RegionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve details and GeoJSON boundary for a specific South Pole region",
)
def get_region(
    region_id: str,
    service: RegionService = Depends(get_region_service),
    frontend: FrontendAdapter = Depends(get_frontend_adapter),
) -> RegionDetailResponse:
    """Return regional coordinates, polygon boundary, and environmental summary for `region_id`."""
    result = service.get_region_detail(region_id)
    return frontend.to_response_payload(result)  # type: ignore[return-value]
