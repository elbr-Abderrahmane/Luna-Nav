"""Pydantic models for Layer 2: Lunar South Pole Regional Exploration.

Represents predefined geographical regions near the Lunar South Pole with
GeoJSON polygon boundaries and preliminary simulated environmental metrics.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.common import (
    DataOrigin,
    GeoJSONPolygonGeometry,
    LunarCoordinates,
    Measurement,
    SimulationBanner,
)


class RegionEnvironmentalSummary(BaseModel):
    """Preliminary geographical and environmental information for a South Pole region card."""

    average_elevation: Measurement = Field(
        ..., description="Average elevation relative to lunar reference sphere (m)."
    )
    average_slope: Measurement = Field(
        ..., description="Preliminary average regional terrain slope (deg)."
    )
    estimated_illumination: Measurement = Field(
        ..., description="Preliminary estimated solar illumination percentage (%)."
    )
    surface_characteristics: str = Field(
        ...,
        min_length=3,
        description="Qualitative description of surface morphology (SIMULATED).",
    )
    preliminary_suitability_label: str = Field(
        default="PROVISIONAL_CANDIDATE_SIMULATED",
        description="Provisional qualitative suitability label (not a validated scientific score).",
    )


class RegionModel(BaseModel):
    """Data model representing a Lunar South Pole exploration region."""

    region_id: str = Field(
        ...,
        min_length=2,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Unique identifier for the South Pole region (e.g., 'reg-shackleton-rim').",
    )
    name: str = Field(..., min_length=2, description="Display name of the South Pole region.")
    description: str = Field(..., description="Overview of the region (marked as MOCK/SIMULATED).")
    data_origin: DataOrigin = Field(default=DataOrigin.MOCK)
    centroid: LunarCoordinates = Field(
        ..., description="Representative center coordinates of the region."
    )
    boundary_geojson: GeoJSONPolygonGeometry = Field(
        ..., description="Highlighted boundary polygon overlaid on the 3D lunar surface."
    )
    environmental_summary: RegionEnvironmentalSummary
    available_zone_count: int = Field(
        default=0, ge=0, description="Number of candidate landing zones mapped inside this region."
    )


class RegionListResponse(BaseModel):
    """Response wrapper for GET /api/regions."""

    count: int = Field(..., ge=0)
    regions: List[RegionModel]
    simulation_banner: SimulationBanner = Field(default_factory=SimulationBanner)


class RegionDetailResponse(BaseModel):
    """Response wrapper for GET /api/regions/{region_id}."""

    region: RegionModel
    recommended_camera_altitude_km: Optional[float] = Field(
        default=45.0,
        gt=0,
        description="Provisional camera zoom altitude hint for Person 1's 3D transition.",
    )
    simulation_banner: SimulationBanner = Field(default_factory=SimulationBanner)
