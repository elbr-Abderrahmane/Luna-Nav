"""Pydantic models for Layer 4: Mission Report Generation & Retrieval.

Defines the input schema capable of receiving all 4 layers' selections and
returning metadata + downloadable PDF report links.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.common import DataOrigin, SimulationBanner


class ReportGenerateRequest(BaseModel):
    """Request payload for POST /api/reports/generate.

    Can be invoked with explicit IDs from Layers 1-4 or use provisional defaults
    so Person 1 (Frontend) and automated tests can generate a complete PDF template
    at any stage of integration.
    """

    mission_id: Optional[str] = Field(
        default=None,
        description="Mission configuration ID from Layer 1 (if omitted, uses default simulated mission).",
    )
    region_id: str = Field(
        default="reg-shackleton-rim",
        min_length=2,
        description="Selected South Pole region ID from Layer 2.",
    )
    compared_zone_ids: List[str] = Field(
        default_factory=lambda: [
            "zone-shackleton-alpha",
            "zone-shackleton-beta",
            "zone-shackleton-gamma",
        ],
        description="The three landing zone IDs compared in Layer 3.",
    )
    recommended_zone_id: Optional[str] = Field(
        default=None,
        description="Winning zone ID from Layer 3 (if omitted, determined via DecisionService).",
    )
    recommended_point_id: Optional[str] = Field(
        default=None,
        description="Optimal landing point ID from Layer 4 (if omitted, determined via DecisionService).",
    )
    include_methodology_and_limitations: bool = Field(
        default=True,
        description="Whether to include scientific data sources, methodology, and mock-data limitations.",
    )

    @field_validator("compared_zone_ids")
    @classmethod
    def validate_three_zones_for_report(cls, v: List[str]) -> List[str]:
        cleaned = [z.strip() for z in v if z and z.strip()]
        if len(cleaned) != 3 or len(set(cleaned)) != 3:
            raise ValueError("Report generation requires exactly 3 distinct compared_zone_ids.")
        return cleaned


class ScientificDataSourceEntry(BaseModel):
    """Metadata describing a scientific module or dataset referenced in the report."""

    domain: str
    owner_role: str
    integration_status: str = Field(default="PROVISIONAL_MOCK_ADAPTER")
    provisional_dataset_label: str
    notes: str


class ReportMetadataResponse(BaseModel):
    """Response model for POST /api/reports/generate and GET /api/reports/{report_id}."""

    report_id: str = Field(..., min_length=3)
    title: str
    generated_at_utc: datetime
    data_origin: DataOrigin = Field(default=DataOrigin.SIMULATED)
    file_name: str
    file_size_bytes: int = Field(..., gt=0)
    content_type: str = Field(default="application/pdf")
    download_url: str = Field(
        ...,
        description="API path to download the generated PDF binary (e.g. /api/reports/{report_id}?format=pdf).",
    )
    mission_id: str
    region_id: str
    compared_zone_ids: List[str]
    recommended_zone_id: str
    recommended_point_id: str
    scientific_data_sources: List[ScientificDataSourceEntry]
    methodology_and_limitations: List[str]
    simulation_banner: SimulationBanner = Field(default_factory=SimulationBanner)
