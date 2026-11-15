"""Scenario Analysis REST Endpoints (`/api/scenarios/*`).

Integrates P3 (`lunanav.astro`), P4 (`lunanav.decision`), and P2 (`lunanav.terrain`)
across Screens 2–5 of the LunaNav application flow (README §6.3–§6.6):
- `POST /api/scenarios/conditions`  (Screen 2: Site View)
- `POST /api/scenarios/timeline`    (Screen 3: Timeline)
- `POST /api/scenarios/compare`     (Screen 4: Side-by-Side Compare + P4 Verdicts & Ranking)
- `POST /api/scenarios/date-sweep`  (Screen 5: 12-Lunar-Day Seasonal Date Sweep + P4 Verdicts)
- `POST /api/scenarios/rank`        (P4 WSM + TOPSIS Multi-Criteria Ranking & Sensitivity Analysis)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.models.scenarios import (
    CompareRequest,
    ConditionsRequest,
    DateSweepRequest,
    RankScenariosRequest,
    TimelineRequest,
)
from app.services.scenario_service import ScenarioService
from lunanav.decision import DecisionInputError

router = APIRouter(prefix="/scenarios", tags=["Screens 2–5 — Scenarios, Astronomy & Verdicts (P3 + P4)"])
scenario_service = ScenarioService()


def _handle_result(result: dict[str, Any]) -> Any:
    """Map P3/P4 error dicts (`status == 'error'`) to HTTP 422 per README §6.7."""
    if result.get("status") == "error":
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content=result)
    return result


@router.post(
    "/conditions",
    summary="Screen 2: Compute Sun/Earth geometry, horizon, power, countdowns, windows, metrics & verdict",
)
def post_scenario_conditions(payload: ConditionsRequest) -> Any:
    try:
        result = scenario_service.compute_conditions(
            site=payload.site,
            start_utc=payload.start_utc,
            window_days=payload.window_days,
            step_h=payload.step_h,
            thresholds=payload.thresholds,
        )
        return _handle_result(result)
    except DecisionInputError as exc:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"status": "error", "error": {"code": exc.code, "message": str(exc)}},
        )


@router.post(
    "/timeline",
    summary="Screen 3: Compute full lunar-day time series and 360-azimuth terrain skyline profile",
)
def post_scenario_timeline(payload: TimelineRequest) -> Any:
    try:
        result = scenario_service.compute_timeline(
            site=payload.site,
            start_utc=payload.start_utc,
            days=payload.days,
            step_h=payload.step_h,
            thresholds=payload.thresholds,
        )
        return _handle_result(result)
    except DecisionInputError as exc:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"status": "error", "error": {"code": exc.code, "message": str(exc)}},
        )


@router.post(
    "/compare",
    summary="Screen 4: Compare 1–12 scenarios side by side with P4 viability verdicts, explanations & ranking",
)
def post_scenario_compare(payload: CompareRequest) -> Any:
    try:
        result = scenario_service.compute_compare(
            scenarios=payload.scenarios,
            window_days=payload.window_days,
            step_h=payload.step_h,
            thresholds=payload.thresholds,
            profile=payload.profile,
        )
        return _handle_result(result)
    except DecisionInputError as exc:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"status": "error", "error": {"code": exc.code, "message": str(exc)}},
        )


@router.post(
    "/date-sweep",
    summary="Screen 5: Sweep consecutive lunar days for a site to evaluate launch slips and polar seasons",
)
def post_scenario_date_sweep(payload: DateSweepRequest) -> Any:
    try:
        result = scenario_service.compute_date_sweep(
            site=payload.site,
            first_start_utc=payload.first_start_utc,
            n=payload.n,
            every_days=payload.every_days,
            window_days=payload.window_days,
            step_h=payload.step_h,
            thresholds=payload.thresholds,
        )
        return _handle_result(result)
    except DecisionInputError as exc:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"status": "error", "error": {"code": exc.code, "message": str(exc)}},
        )


@router.post(
    "/rank",
    summary="P4 Decision Engine: Rank 2..N scenarios using WSM and TOPSIS with weight sensitivity analysis",
)
def post_scenario_rank(payload: RankScenariosRequest) -> Any:
    try:
        result = scenario_service.compute_ranking(
            rows=payload.rows,
            scenarios=payload.scenarios,
            window_days=payload.window_days,
            step_h=payload.step_h,
            profile=payload.profile,
            weights=payload.weights,
            method=payload.method,
            include_sensitivity=payload.include_sensitivity,
        )
        return _handle_result(result)
    except DecisionInputError as exc:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"status": "error", "error": {"code": exc.code, "message": str(exc)}},
        )
