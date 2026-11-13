"""Pydantic models for Layer 4: Optimal Landing-Point Identification & Evaluation.

Represents candidate landing-point markers inside a recommended landing zone and
their detailed local engineering evaluation.
"""

from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from app.models.common import (
    DataOrigin,
    GeoJSONPointGeometry,
    LunarCoordinates,
    Measurement,
    SimulationBanner,
)


class PointEngineeringMetrics(BaseModel):
    """Local engineering and environmental metrics for a specific landing point (Layer 4 marker)."""

    local_slope: Measurement = Field(..., description="Local touchdown slope at the marker (deg).")
    surface_roughness: Measurement = Field(
        ..., description="Local surface roughness at lander footpad scale (m)."
    )
    elevation: Measurement = Field(..., description="Exact point elevation (m).")
    nearest_crater_distance: Measurement = Field(
        ..., description="Distance to the nearest hazardous crater rim (m)."
    )
    nearest_obstacle_distance: Measurement = Field(
        ...,
        description="Distance to nearest boulder/obstacle (m); may be UNAVAILABLE if obstacle map is absent.",
    )
    local_illumination: Measurement = Field(
        ..., description="Simulated local solar illumination percentage (%)."
    )
    earth_visibility: Measurement = Field(
        ..., description="Simulated local direct-to-Earth line-of-sight availability (%)."
    )


class LandingPointModel(BaseModel):
    """Data model representing a candidate landing-point marker on the lunar surface."""

    point_id: str = Field(
        ...,
        min_length=2,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Unique identifier of the candidate landing point (e.g., 'pt-shackleton-a1').",
    )
    zone_id: str = Field(..., min_length=2, description="Parent landing-zone identifier.")
    name: str = Field(..., min_length=2, description="Label for the marker in Layer 4.")
    data_origin: DataOrigin = Field(default=DataOrigin.MOCK)
    coordinates: LunarCoordinates
    point_geojson: GeoJSONPointGeometry
    metrics: PointEngineeringMetrics
    is_provisional_optimal: bool = Field(
        default=False,
        description="Indicates if this marker is flagged as the provisional optimal point in mock data.",
    )


class PointListResponse(BaseModel):
    """Response model for GET /api/zones/{zone_id}/points."""

    zone_id: str
    count: int = Field(..., ge=0)
    recommended_point_id: Optional[str] = Field(
        default=None,
        description="ID of the provisional optimal landing point within the zone.",
    )
    points: List[LandingPointModel]
    simulation_banner: SimulationBanner = Field(default_factory=SimulationBanner)


class PointEvaluateRequest(BaseModel):
    """Request payload for POST /api/points/evaluate.

    Supports evaluating either:
    - A set of candidate points inside a `zone_id` (or explicit `point_ids`), OR
    - A specific user-inspected coordinate pair (`custom_coordinates`) within a zone.
    """

    zone_id: str = Field(..., min_length=2, description="Target landing zone ID.")
    mission_id: Optional[str] = Field(
        default=None,
        description="Optional mission ID for arrival-date illumination/visibility context.",
    )
    point_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional subset of candidate point IDs to evaluate. If omitted, all points in the zone are evaluated.",
    )
    custom_coordinates: Optional[LunarCoordinates] = Field(
        default=None,
        description="Optional custom selenographic coordinates if evaluating an ad-hoc point.",
    )

    @model_validator(mode="after")
    def validate_non_empty_point_ids_if_provided(self) -> "PointEvaluateRequest":
        if self.point_ids is not None and len(self.point_ids) == 0:
            raise ValueError("point_ids cannot be an empty list when provided; omit it to evaluate all zone points.")
        return self


class EvaluatedPointCandidate(BaseModel):
    """Evaluation breakdown for a candidate landing point."""

    point_id: str
    point_name: str
    rank: int = Field(..., ge=1)
    simulated_suitability_score: Measurement = Field(
        ...,
        description="Provisional suitability score [0-100] from Decision Adapter (SIMULATED).",
    )
    passes_engineering_constraints: bool = Field(default=True)
    unavailable_metrics: List[str] = Field(
        default_factory=list,
        description="Metrics marked UNAVAILABLE (kept as None rather than treated as 0).",
    )
    evaluation_notes_simulated: str
    point: LandingPointModel


class PointEvaluationResponse(BaseModel):
    """Response model for POST /api/points/evaluate."""

    evaluation_id: str = Field(..., min_length=3)
    zone_id: str
    mission_id: Optional[str] = None
    data_origin: DataOrigin = Field(default=DataOrigin.SIMULATED)
    recommended_point_id: str
    recommended_coordinates: LunarCoordinates
    recommendation_summary: str
    evaluated_points: List[EvaluatedPointCandidate]
    simulation_banner: SimulationBanner = Field(default_factory=SimulationBanner)
