"""Provisional API routes for Layer 4: PDF Mission Report Generation & Retrieval.

Endpoints:
- POST /api/reports/generate
- GET /api/reports/{report_id} (returns JSON metadata by default, or PDF file when `?format=pdf`)
"""

from typing import Literal, Optional, Union

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse

from app.integrations.frontend_adapter import FrontendAdapter, get_frontend_adapter
from app.models.report import ReportGenerateRequest, ReportMetadataResponse
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Layer 4 — Mission Reports"])


def get_report_service() -> ReportService:
    """Dependency provider for ReportService."""
    return ReportService()


@router.post(
    "/generate",
    response_model=ReportMetadataResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a provisional mission PDF report (marked MOCK/SIMULATED)",
)
def generate_report(
    payload: Optional[ReportGenerateRequest] = None,
    report_service: ReportService = Depends(get_report_service),
    frontend: FrontendAdapter = Depends(get_frontend_adapter),
) -> ReportMetadataResponse:
    """Generate a PDF report from mission, region, zone comparison, and landing-point selections."""
    request_model = payload or ReportGenerateRequest()
    result = report_service.generate_report(request_model)
    return frontend.to_response_payload(result)  # type: ignore[return-value]


@router.get(
    "/{report_id}",
    response_model=ReportMetadataResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve report metadata or download PDF binary (?format=pdf)",
)
def get_report(
    report_id: str,
    format: Literal["json", "pdf"] = Query(
        default="json",
        description="Return 'json' report metadata (default) or 'pdf' downloadable binary.",
    ),
    report_service: ReportService = Depends(get_report_service),
    frontend: FrontendAdapter = Depends(get_frontend_adapter),
) -> Union[ReportMetadataResponse, FileResponse]:
    """Retrieve report metadata as JSON, or download the generated PDF file when `format=pdf`."""
    if format == "pdf":
        metadata, pdf_path = report_service.get_report_pdf_path(report_id)
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=metadata.file_name,
        )
    result = report_service.get_report_metadata(report_id)
    return frontend.to_response_payload(result)  # type: ignore[return-value]
