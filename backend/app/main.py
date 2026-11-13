"""LUNA NAV — FastAPI Backend Application Entrypoint.

Wires together:
- Provisional REST endpoints across Layers 1–4 (`/api/...`)
- Health check endpoint (`GET /health`)
- CORS middleware for Person 1's 3D Frontend
- Unified exception handling (`app/core/exceptions.py`)
"""

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.api import mission, points, regions, reports, zones
from app.core.config import settings
from app.core.exceptions import register_exception_handlers


def create_app() -> FastAPI:
    """Application factory for the LUNA NAV Backend Foundation."""
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Provisional modular backend and integration foundation for **LUNA NAV** "
            "(NASA Lunar Landing Site Navigator). Operates independently with clearly labeled "
            "`MOCK` / `SIMULATED` datasets and adapter interfaces while awaiting specifications "
            "from Persons 1, 2, 3, and 4."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS for Person 1's 3D Frontend
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register domain and validation exception handlers
    register_exception_handlers(application)

    # Health check endpoint (root level as requested: GET /health)
    @application.get(
        "/health",
        status_code=status.HTTP_200_OK,
        tags=["System Health"],
        summary="Check backend health and external module adapter modes",
    )
    def health_check() -> Dict[str, Any]:
        return {
            "status": "ok",
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "adapters": {
                "terrain_gis_person_2": "MOCK" if settings.use_mock_terrain else "REAL_STUB",
                "astronomy_orbital_person_3": "MOCK" if settings.use_mock_astronomy else "REAL_STUB",
                "decision_engine_person_4": "MOCK" if settings.use_mock_decision else "REAL_STUB",
                "frontend_presenter_person_1": "PROVISIONAL",
            },
            "data_origin": "MOCK_AND_SIMULATED",
        }

    # Mount Layer 1–4 API routers under /api
    api_prefix = settings.api_prefix
    application.include_router(mission.router, prefix=api_prefix)
    application.include_router(regions.router, prefix=api_prefix)
    application.include_router(zones.router, prefix=api_prefix)
    application.include_router(points.router, prefix=api_prefix)
    application.include_router(reports.router, prefix=api_prefix)

    return application


app = create_app()
