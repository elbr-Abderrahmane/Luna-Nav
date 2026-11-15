"""Site Catalog REST Endpoints (`GET /api/sites`, `GET /api/sites/{site_id}`).

Wraps P3's 26-site lunar catalog (`lunanav.astro.sites`) per README §6.2.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse

from app.services.scenario_service import ScenarioService

router = APIRouter(prefix="/sites", tags=["Screen 1 — Lunar Site Catalog (P3)"])
scenario_service = ScenarioService()


@router.get(
    "",
    summary="List the 26-site lunar landing catalog (optionally filtered by category)",
)
def list_lunar_sites(
    category: Optional[str] = Query(
        default=None,
        description="Filter by site category: apollo, artemis, clps, international, south_pole_candidate, reference",
    ),
) -> Any:
    result = scenario_service.get_sites(category=category)
    if result.get("status") == "error":
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content=result)
    return result


@router.get(
    "/{site_id}",
    summary="Retrieve a single lunar landing site by its catalog ID",
)
def get_lunar_site(site_id: str) -> Any:
    result: Dict[str, Any] = scenario_service.get_site_by_id(site_id)
    if result.get("status") == "error":
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=result)
    return result

