"""Report Service for Layer 4: PDF Mission Report Generation & Retrieval.

Proposes and uses `reportlab` (pure-Python PDF engine with zero system-level C library
dependencies) to generate a structured PDF report template populated with mock/simulated
mission, region, 3-zone comparison, and landing-point data.
Includes a pure-Python minimal PDF fallback if `reportlab` is ever unavailable.
"""

import io
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.exceptions import ResourceNotFoundError
from app.models.common import DataOrigin, Measurement
from app.models.mission import MissionResponse
from app.models.point import PointEvaluateRequest, PointEvaluationResponse
from app.models.region import RegionModel
from app.models.report import (
    ReportGenerateRequest,
    ReportMetadataResponse,
    ScientificDataSourceEntry,
)
from app.models.zone import ZoneComparisonRequest, ZoneComparisonResponse
from app.services.decision_service import DecisionService
from app.services.mission_service import DEFAULT_MOCK_MISSION_ID, MissionService
from app.services.terrain_service import TerrainService

logger = logging.getLogger("luna_nav.services.report")

# In-memory registry of generated reports and their on-disk PDF paths
_REPORT_METADATA_STORE: Dict[str, ReportMetadataResponse] = {}
_REPORT_FILE_STORE: Dict[str, Path] = {}


def _format_measurement(m: Optional[Measurement]) -> str:
    """Format a Measurement for PDF display, preserving UNAVAILABLE explicitly (never 0)."""
    if m is None:
        return "UNAVAILABLE (null)"
    if m.value is None or m.status.value == "UNAVAILABLE":
        return f"UNAVAILABLE (not 0) [{m.unit}]"
    return f"{m.value} {m.unit} ({m.status.value})"


class ReportService:
    """Service responsible for assembling mission results and rendering the PDF report."""

    def __init__(
        self,
        mission_service: Optional[MissionService] = None,
        terrain_service: Optional[TerrainService] = None,
        decision_service: Optional[DecisionService] = None,
        output_dir: Optional[Path] = None,
    ) -> None:
        self.mission_service = mission_service or MissionService()
        self.terrain_service = terrain_service or TerrainService()
        self.decision_service = decision_service or DecisionService(
            terrain_service=self.terrain_service,
            mission_service=self.mission_service,
        )
        self.output_dir = output_dir or settings.reports_output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(self, request: ReportGenerateRequest) -> ReportMetadataResponse:
        """Assemble Layer 1-4 data and render a provisional PDF report clearly marked SIMULATED."""
        mission_id = request.mission_id or DEFAULT_MOCK_MISSION_ID
        mission: MissionResponse = self.mission_service.get_mission(mission_id)
        region: RegionModel = self.terrain_service.get_region_by_id(request.region_id)

        zone_comparison: ZoneComparisonResponse = self.decision_service.compare_three_zones(
            ZoneComparisonRequest(
                mission_id=mission.mission_id,
                region_id=region.region_id,
                zone_ids=request.compared_zone_ids,
            )
        )

        winning_zone_id = request.recommended_zone_id or zone_comparison.recommended_zone_id
        point_evaluation: PointEvaluationResponse = self.decision_service.evaluate_points(
            PointEvaluateRequest(
                zone_id=winning_zone_id,
                mission_id=mission.mission_id,
            )
        )

        winning_point_id = request.recommended_point_id or point_evaluation.recommended_point_id

        report_id = f"rep-{uuid.uuid4().hex[:8]}"
        generated_at = datetime.now(timezone.utc)
        file_name = f"luna_nav_report_{report_id}.pdf"
        file_path = self.output_dir / file_name

        sources = self._build_scientific_sources()
        methodology_notes = [
            "SIMULATED REPORT NOTICE: All numerical values, coordinates, and rankings in this report are provisional MOCK / SIMULATED placeholders.",
            "Missing scientific parameters (such as unmapped boulder density or sub-meter obstacle clearance) are explicitly represented as UNAVAILABLE (null) and are never treated as zero.",
            "Orbital trajectory, solar illumination, and Earth visibility await Person 3's Astronomy & Orbital Mechanics module.",
            "Regional DEM slope, roughness, and crater/boulder GIS extraction await Person 2's Terrain Analysis module.",
            "Multi-criteria weighting and landing-site optimization await Person 4's Decision Engine specification.",
        ]

        pdf_bytes = self._render_pdf_bytes(
            report_id=report_id,
            generated_at=generated_at,
            mission=mission,
            region=region,
            zone_comparison=zone_comparison,
            point_evaluation=point_evaluation,
            sources=sources,
            methodology_notes=methodology_notes if request.include_methodology_and_limitations else [],
        )
        file_path.write_bytes(pdf_bytes)

        metadata = ReportMetadataResponse(
            report_id=report_id,
            title=f"LUNA NAV Mission Site Selection Report — {mission.mission_name} (SIMULATED)",
            generated_at_utc=generated_at,
            data_origin=DataOrigin.SIMULATED,
            file_name=file_name,
            file_size_bytes=len(pdf_bytes),
            content_type="application/pdf",
            download_url=f"{settings.api_prefix}/reports/{report_id}?format=pdf",
            mission_id=mission.mission_id,
            region_id=region.region_id,
            compared_zone_ids=request.compared_zone_ids,
            recommended_zone_id=winning_zone_id,
            recommended_point_id=winning_point_id,
            scientific_data_sources=sources,
            methodology_and_limitations=methodology_notes,
        )

        _REPORT_METADATA_STORE[report_id] = metadata
        _REPORT_FILE_STORE[report_id] = file_path
        logger.info("Generated PDF report %s (%d bytes) at %s", report_id, len(pdf_bytes), file_path)
        return metadata

    def get_report_metadata(self, report_id: str) -> ReportMetadataResponse:
        """Retrieve metadata for a generated report by ID."""
        metadata = _REPORT_METADATA_STORE.get(report_id)
        if not metadata:
            raise ResourceNotFoundError(resource_type="Report", resource_id=report_id)
        return metadata

    def get_report_pdf_path(self, report_id: str) -> Tuple[ReportMetadataResponse, Path]:
        """Return both metadata and on-disk PDF path for downloading."""
        metadata = self.get_report_metadata(report_id)
        file_path = _REPORT_FILE_STORE.get(report_id)
        if not file_path or not file_path.exists():
            raise ResourceNotFoundError(resource_type="ReportFile", resource_id=report_id)
        return metadata, file_path

    @staticmethod
    def _build_scientific_sources() -> List[ScientificDataSourceEntry]:
        return [
            ScientificDataSourceEntry(
                domain="Frontend & 3D Visualization",
                owner_role="Person 1",
                integration_status="PROVISIONAL_MOCK_ADAPTER",
                provisional_dataset_label="FrontendAdapter (Layer 1-4 JSON & GeoJSON envelopes)",
                notes="Awaiting final 3D scene camera and HUD schema confirmation.",
            ),
            ScientificDataSourceEntry(
                domain="Terrain Analysis & GIS",
                owner_role="Person 2",
                integration_status="PROVISIONAL_MOCK_ADAPTER",
                provisional_dataset_label="MockTerrainAdapter (app/mock_data/regions, zones, points)",
                notes="Awaiting LOLA DEM slope/roughness and crater/boulder GIS outputs.",
            ),
            ScientificDataSourceEntry(
                domain="Astronomy & Orbital Mechanics",
                owner_role="Person 3",
                integration_status="PROVISIONAL_MOCK_ADAPTER",
                provisional_dataset_label="MockAstronomyAdapter (Simulated transfer & lighting)",
                notes="Awaiting Earth-Moon ephemeris, illumination, and DTE visibility solver.",
            ),
            ScientificDataSourceEntry(
                domain="Decision Engine & Optimization",
                owner_role="Person 4",
                integration_status="PROVISIONAL_MOCK_ADAPTER",
                provisional_dataset_label="MockDecisionAdapter (Deterministic placeholder lookup)",
                notes="Awaiting multi-criteria weights and ranking specification.",
            ),
        ]

    @staticmethod
    def _render_pdf_bytes(
        report_id: str,
        generated_at: datetime,
        mission: MissionResponse,
        region: RegionModel,
        zone_comparison: ZoneComparisonResponse,
        point_evaluation: PointEvaluationResponse,
        sources: List[ScientificDataSourceEntry],
        methodology_notes: List[str],
    ) -> bytes:
        """Render the PDF report using ReportLab (with a minimal PDF fallback)."""
        lines: List[str] = [
            "==========================================================================",
            "LUNA NAV — LUNAR SOUTH POLE LANDING SITE NAVIGATOR MISSION REPORT",
            "STATUS: PROVISIONAL TEMPLATE — MOCK / SIMULATED DATA ONLY",
            "==========================================================================",
            f"Report ID: {report_id}",
            f"Generated (UTC): {generated_at.isoformat()}",
            "Disclaimer: NOT derived from validated NASA observations or final team modules.",
            "",
            "1. LAYER 1 — MISSION CONFIGURATION & EARTH-MOON INTERCEPTION (SIMULATED)",
            f"   Mission ID: {mission.mission_id} | Name: {mission.mission_name}",
            f"   Estimated Launch (UTC): {mission.interception_window.estimated_launch_utc.isoformat()}",
            f"   Confirmed Arrival (UTC): {mission.interception_window.confirmed_arrival_utc.isoformat()}",
            f"   Interception Window: {mission.interception_window.window_start_utc.isoformat()} to {mission.interception_window.window_end_utc.isoformat()}",
            f"   Earth-Moon Distance: {_format_measurement(mission.orbital_parameters.earth_moon_distance)}",
            f"   Transfer Duration: {_format_measurement(mission.orbital_parameters.estimated_transfer_duration)}",
            f"   Sub-Solar Longitude: {_format_measurement(mission.orbital_parameters.solar_sub_longitude)}",
            "",
            "2. LAYER 2 — SELECTED LUNAR SOUTH POLE REGION (MOCK)",
            f"   Region ID: {region.region_id} | Name: {region.name}",
            f"   Centroid: ({region.centroid.latitude} deg, {region.centroid.longitude} deg)",
            f"   Avg Elevation: {_format_measurement(region.environmental_summary.average_elevation)}",
            f"   Avg Slope: {_format_measurement(region.environmental_summary.average_slope)}",
            f"   Est. Illumination: {_format_measurement(region.environmental_summary.estimated_illumination)}",
            "",
            "3. LAYER 3 — THREE-ZONE COMPARATIVE EVALUATION (SIMULATED)",
            f"   Recommended Landing Zone ID: {zone_comparison.recommended_zone_id}",
        ]

        for cand in zone_comparison.ranked_candidates:
            p = cand.zone_details.parameters
            lines.append(
                f"   - Rank #{cand.rank}: {cand.zone_name} ({cand.zone_id}) | "
                f"Mock Score: {_format_measurement(cand.simulated_suitability_score)}"
            )
            lines.append(
                f"     Avg Slope: {_format_measurement(p.average_slope)} | "
                f"Roughness: {_format_measurement(p.surface_roughness)} | "
                f"Boulder Density: {_format_measurement(p.boulder_density)}"
            )
            if cand.unavailable_metrics:
                lines.append(
                    f"     Unavailable Metrics (kept as null, not 0): {', '.join(cand.unavailable_metrics)}"
                )

        lines.extend(
            [
                "",
                "4. LAYER 4 — OPTIMAL LANDING-POINT IDENTIFICATION (SIMULATED)",
                f"   Recommended Point ID: {point_evaluation.recommended_point_id}",
                f"   Recommended Coordinates: ({point_evaluation.recommended_coordinates.latitude} deg, "
                f"{point_evaluation.recommended_coordinates.longitude} deg)",
            ]
        )

        for pt_cand in point_evaluation.evaluated_points:
            m = pt_cand.point.metrics
            lines.append(
                f"   - Rank #{pt_cand.rank}: {pt_cand.point_name} ({pt_cand.point_id}) | "
                f"Score: {_format_measurement(pt_cand.simulated_suitability_score)}"
            )
            lines.append(
                f"     Local Slope: {_format_measurement(m.local_slope)} | "
                f"Obstacle Dist: {_format_measurement(m.nearest_obstacle_distance)} | "
                f"Illumination: {_format_measurement(m.local_illumination)}"
            )

        lines.extend(["", "5. SCIENTIFIC DATA SOURCES & INTEGRATION STATUS"])
        for src in sources:
            lines.append(f"   - [{src.owner_role}] {src.domain}: {src.integration_status} ({src.notes})")

        if methodology_notes:
            lines.extend(["", "6. METHODOLOGY & LIMITATIONS"])
            for note in methodology_notes:
                lines.append(f"   * {note}")

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas

            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            c.setTitle(f"LUNA NAV Report {report_id} (SIMULATED)")
            c.setAuthor("LUNA NAV Backend Foundation")

            y = height - 40
            c.setFont("Helvetica-Bold", 10)
            for line in lines:
                if y < 50:
                    c.showPage()
                    c.setFont("Helvetica", 8)
                    y = height - 40
                if line.startswith("===") or line.startswith("LUNA NAV") or line.startswith("STATUS:"):
                    c.setFont("Helvetica-Bold", 9)
                elif line[:2] in ("1.", "2.", "3.", "4.", "5.", "6."):
                    c.setFont("Helvetica-Bold", 9)
                else:
                    c.setFont("Helvetica", 8)
                c.drawString(36, y, line[:115])
                y -= 12

            c.save()
            return buffer.getvalue()
        except ImportError:
            # Minimal valid PDF 1.4 fallback if reportlab is not installed
            text_payload = "\\n".join(lines)
            stream_content = f"BT /F1 9 Tf 36 750 Td ({text_payload[:1500]}) Tj ET".encode("latin-1", "replace")
            return (
                b"%PDF-1.4\n"
                b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
                b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
                b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >> endobj\n"
                + f"4 0 obj << /Length {len(stream_content)} >> stream\n".encode("ascii")
                + stream_content
                + b"\nendstream endobj\n"
                b"xref\n0 5\n0000000000 65535 f \n"
                b"trailer << /Root 1 0 R /Size 5 >>\nstartxref\n0\n%%EOF\n"
            )
