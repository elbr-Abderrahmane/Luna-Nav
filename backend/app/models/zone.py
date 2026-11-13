"""Pydantic models for Layer 3: Landing-Zone Identification & Evaluation.

Includes:
- Candidate landing-zone polygon and engineering/environmental metrics (with explicit
  support for unavailable parameters such as boulder density).
- Strict validation of selecting EXACTLY THREE distinct landing zones for comparison.
"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.common import (
    DataOrigin,
    GeoJSONPolygonGeometry,
    LunarCoordinates,
    Measurement,
    SimulationBanner,
)


class ZoneEngineeringParameters(BaseModel):
    """Detailed engineering and environmental parameters for a landing zone (Layer 3 card).

    Note: Missing measurements (e.g. `boulder_density` when high-res imagery is unavailable)
    are represented with `value=None` and `status="UNAVAILABLE"`, NEVER as `0.0`.
    """

    average_slope: Measurement = Field(..., description="Average terrain slope across the zone (deg).")
    max_slope: Measurement = Field(..., description="Maximum local slope within the zone (deg).")
    surface_roughness: Measurement = Field(
        ..., description="Root-mean-square surface roughness (m)."
    )
    elevation: Measurement = Field(..., description="Mean zone elevation (m).")
    crater_density: Measurement = Field(
        ..., description="Crater spatial density (craters/km^2)."
    )
    boulder_density: Measurement = Field(
        ...,
        description="Boulder spatial density (boulders/km^2); may be UNAVAILABLE if NAC data is absent.",
    )
    illumination_percentage: Measurement = Field(
        ..., description="Simulated solar illumination percentage during mission window (%)."
    )
    earth_visibility_percentage: Measurement = Field(
        ..., description="Simulated direct-to-Earth communication visibility (%)."
    )
    safety_notes: str = Field(
        default="SIMULATED engineering parameters; awaiting Person 2 & Person 3 modules.",
        description="Additional landing-safety context.",
    )


class LandingZoneModel(BaseModel):
    """Data model representing a candidate landing zone polygon within a South Pole region."""

    zone_id: str = Field(
        ...,
        min_length=2,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Unique identifier of the landing zone (e.g., 'zone-shackleton-alpha').",
    )
    region_id: str = Field(
        ...,
        min_length=2,
        description="Parent region_id to which this landing zone belongs.",
    )
    name: str = Field(..., min_length=2, description="Human-readable name of the landing zone.")
    data_origin: DataOrigin = Field(default=DataOrigin.MOCK)
    centroid: LunarCoordinates
    area_km2: Measurement = Field(..., description="Approximate surface area of the polygon (km^2).")
    polygon_geojson: GeoJSONPolygonGeometry = Field(
        ..., description="GeoJSON Polygon boundary displayed on the 3D lunar terrain."
    )
    parameters: ZoneEngineeringParameters


class ZoneListResponse(BaseModel):
    """Response model for GET /api/regions/{region_id}/zones."""

    region_id: str
    count: int = Field(..., ge=0)
    zones: List[LandingZoneModel]
    simulation_banner: SimulationBanner = Field(default_factory=SimulationBanner)


class ZoneComparisonRequest(BaseModel):
    """Request payload for POST /api/zones/compare.

    Enforces the LUNA NAV Layer 3 workflow rule: the user MUST select EXACTLY THREE
    distinct candidate landing zones for comparative evaluation.
    """

    mission_id: Optional[str] = Field(
        default=None,
        description="Optional mission_id to contextualize illumination/visibility during comparison.",
    )
    region_id: Optional[str] = Field(
        default=None,
        description="Optional region_id to verify all selected zones belong to the active region.",
    )
    zone_ids: List[str] = Field(
        ...,
        description="List of exactly three distinct landing-zone IDs selected by the user.",
    )

    @field_validator("zone_ids")
    @classmethod
    def validate_exactly_three_unique_zones(cls, zone_ids: List[str]) -> List[str]:
        cleaned = [zid.strip() for zid in zone_ids if zid and zid.strip()]
        if len(cleaned) != 3:
            raise ValueError(
                f"Exactly 3 landing zones must be selected for comparison; received {len(cleaned)}."
            )
        if len(set(cleaned)) != 3:
            raise ValueError(
                "All 3 selected landing zones must have distinct zone_ids (duplicates are not allowed)."
            )
        return cleaned


class RankedZoneCandidate(BaseModel):
    """Comparative evaluation result for a single zone in a 3-zone comparison."""

    zone_id: str
    zone_name: str
    rank: int = Field(..., ge=1, le=3, description="Relative rank among the 3 candidates (1 = best).")
    simulated_suitability_score: Measurement = Field(
        ...,
        description="Provisional placeholder score [0-100] from Decision Adapter (SIMULATED).",
    )
    eligible: bool = Field(
        default=True,
        description="Whether the zone satisfies provisional engineering constraints.",
    )
    unavailable_metrics: List[str] = Field(
        default_factory=list,
        description="List of metric names that were UNAVAILABLE and therefore excluded from zero-imputation.",
    )
    rationale_simulated: str = Field(
        ...,
        description="Simulated explanation of strengths/trade-offs for this candidate.",
    )
    zone_details: LandingZoneModel


class ZoneComparisonResponse(BaseModel):
    """Response model for POST /api/zones/compare."""

    comparison_id: str = Field(..., min_length=3)
    mission_id: Optional[str] = None
    region_id: Optional[str] = None
    data_origin: DataOrigin = Field(default=DataOrigin.SIMULATED)
    recommended_zone_id: str = Field(
        ..., description="The highest-ranked eligible landing zone ID."
    )
    comparison_summary: str = Field(
        ...,
        description="Explanation of why the recommended zone ranked highest (marked SIMULATED).",
    )
    scoring_methodology_note: str = Field(
        default=(
            "PROVISIONAL MOCK RANKING: Uses deterministic placeholder comparison in DecisionAdapter. "
            "Final multi-criteria scoring weights and optimization belong to Person 4."
        )
    )
    ranked_candidates: List[RankedZoneCandidate] = Field(..., min_length=3, max_length=3)
    simulation_banner: SimulationBanner = Field(default_factory=SimulationBanner)
