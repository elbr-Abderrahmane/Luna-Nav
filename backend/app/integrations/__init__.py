"""External module integration adapters for LUNA NAV (Persons 1, 2, 3, and 4)."""

from app.integrations.astronomy_adapter import (
    BaseAstronomyAdapter,
    MockAstronomyAdapter,
    RealAstronomyAdapterStub,
    get_astronomy_adapter,
)
from app.integrations.decision_adapter import (
    BaseDecisionAdapter,
    MockDecisionAdapter,
    RealDecisionAdapterStub,
    get_decision_adapter,
)
from app.integrations.frontend_adapter import FrontendAdapter, get_frontend_adapter
from app.integrations.terrain_adapter import (
    BaseTerrainAdapter,
    MockTerrainAdapter,
    RealTerrainAdapterStub,
    get_terrain_adapter,
)

__all__ = [
    "BaseAstronomyAdapter",
    "BaseDecisionAdapter",
    "BaseTerrainAdapter",
    "FrontendAdapter",
    "MockAstronomyAdapter",
    "MockDecisionAdapter",
    "MockTerrainAdapter",
    "RealAstronomyAdapterStub",
    "RealDecisionAdapterStub",
    "RealTerrainAdapterStub",
    "get_astronomy_adapter",
    "get_decision_adapter",
    "get_frontend_adapter",
    "get_terrain_adapter",
]
