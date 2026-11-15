"""Scenario Comparison Export Endpoint (`POST /api/export`).

Exports a scenario comparison (with P4 verdicts and P3 metrics) as CSV or JSON (README §6.7).
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse

from app.models.scenarios import ExportRequest
from app.services.scenario_service import ScenarioService
from lunanav.decision import DecisionInputError

router = APIRouter(prefix="/export", tags=["Comparison Export (P5)"])
scenario_service = ScenarioService()


@router.post(
    "",
    summary="Export a scenario comparison table as CSV or JSON",
)
def export_comparison(payload: ExportRequest) -> Any:
    compare_data = payload.compare_data
    if compare_data is None:
        if not payload.scenarios:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                content={
                    "status": "error",
                    "error": {
                        "code": "INVALID_EXPORT_REQUEST",
                        "message": "Provide either 'compare_data' or 'scenarios' to export.",
                    },
                },
            )
        try:
            compare_data = scenario_service.compute_compare(
                scenarios=payload.scenarios,
                thresholds=payload.thresholds,
            )
        except DecisionInputError as exc:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                content={"status": "error", "error": {"code": exc.code, "message": str(exc)}},
            )
        if compare_data.get("status") == "error":
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                content=compare_data,
            )

    if payload.format == "json":
        body = json.dumps(compare_data, indent=2)
        return Response(
            content=body,
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="lunanav_comparison.json"'},
        )

    csv_text = scenario_service.export_comparison_csv(compare_data)
    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="lunanav_comparison.csv"'},
    )

