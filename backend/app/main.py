"""LUNA NAV — FastAPI Full-Stack Backend Application Entrypoint.

Wires together all 5 team modules:
- Screen 1–5 Scenario Flow (`/api/sites`, `/api/scenarios/*`, `/api/terrain/*`, `/api/explainers`, `/api/export`)
  powered by P2 (`lunanav.terrain`), P3 (`lunanav.astro`), and P4 (`lunanav.decision`)
- Legacy Layer 1–4 endpoints (`/api/mission`, `/api/regions`, `/api/zones`, `/api/points`, `/api/reports`)
- Health check endpoints (`GET /health` and `GET /api/health`)
- CORS middleware for P1's React + TypeScript Frontend (`frontend/`)
- Unified exception handling (`app/core/exceptions.py`)
"""

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    explainers,
    export,
    mission,
    points,
    regions,
    reports,
    scenarios,
    sites,
    terrain,
    zones,
)
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from lunanav.astro.ephemeris import get_ephemeris
from lunanav.terrain.dem import default_dem_path


def _build_health_payload() -> Dict[str, Any]:
    try:
        eph = get_ephemeris()
        eph_info = {"backend": eph.name, "source": eph.source}
    except Exception:
        eph_info = {"backend": "analytic", "source": "Meeus"}

    dem_file = default_dem_path()
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "modules": {
            "p1_frontend": "READY",
            "p2_terrain": "ACTIVE (LOLA DEM loaded)" if dem_file.is_file() else "ACTIVE (smooth-sphere fallback)",
            "p3_astronomy": f"ACTIVE ({eph_info['backend']}: {eph_info['source']})",
            "p4_decision": "ACTIVE (verdict + WSM/TOPSIS ranking + explainers)",
            "p5_backend": "ACTIVE",
        },
        "adapters": {
            "terrain_gis_person_2": "MOCK" if settings.use_mock_terrain else "REAL_STUB",
            "astronomy_orbital_person_3": "MOCK" if settings.use_mock_astronomy else "REAL_STUB",
            "decision_engine_person_4": "MOCK" if settings.use_mock_decision else "REAL_STUB",
            "frontend_presenter_person_1": "PROVISIONAL",
        },
        "data_origin": "MOCK_AND_SIMULATED",
    }


def create_app() -> FastAPI:
    """Application factory for the LUNA NAV Full-Stack Backend."""
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Full-stack backend for **LUNA NAV** (NASA Space Apps 2026 — Lunar Landing Site Navigator). "
            "Integrates P2 (`lunanav.terrain`), P3 (`lunanav.astro`), and P4 (`lunanav.decision`) "
            "to serve P1's React + TypeScript frontend."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS for Person 1's Frontend
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register domain and validation exception handlers
    register_exception_handlers(application)

    # Health check endpoints (GET /health and GET /api/health)
    @application.get(
        "/health",
        status_code=status.HTTP_200_OK,
        tags=["System Health"],
        summary="Check backend health and active scientific modules",
    )
    def health_check() -> Dict[str, Any]:
        return _build_health_payload()

    @application.get(
        f"{settings.api_prefix}/health",
        status_code=status.HTTP_200_OK,
        tags=["System Health"],
        summary="Check backend health under /api/health",
    )
    def api_health_check() -> Dict[str, Any]:
        return _build_health_payload()

    # Mount primary Scenario Flow routers (Screens 1–5 + P2 Terrain + P4 Explainers + P5 Export)
    api_prefix = settings.api_prefix
    application.include_router(sites.router, prefix=api_prefix)
    application.include_router(scenarios.router, prefix=api_prefix)
    application.include_router(terrain.router, prefix=api_prefix)
    application.include_router(explainers.router, prefix=api_prefix)
    application.include_router(export.router, prefix=api_prefix)

    # Mount legacy Layer 1–4 routers for backward compatibility
    application.include_router(mission.router, prefix=api_prefix)
    application.include_router(regions.router, prefix=api_prefix)
    application.include_router(zones.router, prefix=api_prefix)
    application.include_router(points.router, prefix=api_prefix)
    application.include_router(reports.router, prefix=api_prefix)

    return application


app = create_app()
