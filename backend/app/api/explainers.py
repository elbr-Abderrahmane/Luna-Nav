"""Public Educational Explainers REST Endpoints (`/api/explainers`).

Serves P4's markdown explainers (`docs/explainers/*.md`) per README §6.7.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.models.scenarios import ExplainerItem, ExplainersResponse
from app.services.explainer_service import ExplainerService

router = APIRouter(prefix="/explainers", tags=["Public Explainers (P4)"])
explainer_service = ExplainerService()


@router.get(
    "",
    response_model=ExplainersResponse,
    summary="List all public astronomy & decision explainers (Sunlight, Earth visibility, Lunar day, Libration, Verdicts)",
)
def list_all_explainers() -> ExplainersResponse:
    return explainer_service.list_explainers()


@router.get(
    "/{explainer_id}",
    response_model=ExplainerItem,
    summary="Get a single public explainer by ID",
)
def get_single_explainer(explainer_id: str) -> ExplainerItem:
    return explainer_service.get_explainer(explainer_id)

