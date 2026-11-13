"""Shared Pydantic validation primitives for LUNA NAV.

Includes:
- Explicit representation of data origin (MOCK / SIMULATED vs. future REAL module output).
- Explicit representation of unavailable scientific measurements (None + UNAVAILABLE status,
  never silently coerced to zero).
- Coordinate and GeoJSON geometry validation (Point and Polygon).
"""

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class DataOrigin(str, Enum):
    """Identifies whether data comes from a provisional mock dataset/adapter or a real module."""

    MOCK = "MOCK"
    SIMULATED = "SIMULATED"
    PROVISIONAL_ADAPTER = "PROVISIONAL_ADAPTER"


class MeasurementStatus(str, Enum):
    """Explicit availability state for scientific and engineering measurements."""

    SIMULATED = "SIMULATED"
    UNAVAILABLE = "UNAVAILABLE"


class Measurement(BaseModel):
    """Numeric measurement with explicit unit and availability status.

    Rule: Missing or unmeasured scientific parameters (e.g., boulder density where
    high-resolution imagery is not yet integrated) MUST have `value=None` and
    `status=MeasurementStatus.UNAVAILABLE`. They must NEVER default to 0.
    """

    value: Optional[float] = Field(
        default=None,
        description="Numeric value of the measurement, or None if the measurement is unavailable.",
    )
    unit: str = Field(
        ...,
        min_length=1,
        description="Physical unit of the measurement (e.g., 'deg', 'm', 'km', '%', 'craters/km^2').",
    )
    status: MeasurementStatus = Field(
        default=MeasurementStatus.SIMULATED,
        description="Explicit availability status (SIMULATED or UNAVAILABLE).",
    )
    note: Optional[str] = Field(
        default=None,
        description="Contextual note explaining mock origin or why data is unavailable.",
    )

    @model_validator(mode="after")
    def validate_availability_consistency(self) -> "Measurement":
        """Ensure missing values and UNAVAILABLE status are strictly consistent."""
        if self.value is None and self.status != MeasurementStatus.UNAVAILABLE:
            self.status = MeasurementStatus.UNAVAILABLE
        if self.status == MeasurementStatus.UNAVAILABLE and self.value is not None:
            raise ValueError(
                "A measurement marked as UNAVAILABLE must have value=None (do not represent missing data as a number)."
            )
        return self


class LunarCoordinates(BaseModel):
    """Lunar selenographic coordinates with strict latitude/longitude validation."""

    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Selenographic latitude in decimal degrees [-90.0, 90.0]. South Pole is near -90.0.",
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Selenographic longitude in decimal degrees [-180.0, 180.0].",
    )
    elevation_m: Optional[Measurement] = Field(
        default=None,
        description="Local surface elevation in meters relative to lunar reference sphere.",
    )


class GeoJSONPointGeometry(BaseModel):
    """Valid GeoJSON Point geometry: [longitude, latitude] or [longitude, latitude, elevation]."""

    type: Literal["Point"] = "Point"
    coordinates: List[float] = Field(
        ...,
        min_length=2,
        max_length=3,
        description="[longitude, latitude] or [longitude, latitude, elevation_m]",
    )

    @field_validator("coordinates")
    @classmethod
    def validate_point_coordinates(cls, coords: List[float]) -> List[float]:
        lon, lat = coords[0], coords[1]
        if not (-180.0 <= lon <= 180.0):
            raise ValueError(f"GeoJSON Point longitude must be between -180 and 180, got {lon}")
        if not (-90.0 <= lat <= 90.0):
            raise ValueError(f"GeoJSON Point latitude must be between -90 and 90, got {lat}")
        return coords


class GeoJSONPolygonGeometry(BaseModel):
    """Valid GeoJSON Polygon geometry with closed linear rings and valid lunar coordinates."""

    type: Literal["Polygon"] = "Polygon"
    coordinates: List[List[List[float]]] = Field(
        ...,
        min_length=1,
        description="List of linear rings; each ring is a list of [lon, lat] coordinate pairs.",
    )

    @field_validator("coordinates")
    @classmethod
    def validate_polygon_rings(cls, rings: List[List[List[float]]]) -> List[List[List[float]]]:
        for ring_idx, ring in enumerate(rings):
            if len(ring) < 4:
                raise ValueError(
                    f"GeoJSON Polygon ring {ring_idx} must have at least 4 positions (closed triangle minimum)."
                )
            for pos in ring:
                if len(pos) < 2:
                    raise ValueError("Each GeoJSON position must have at least [longitude, latitude].")
                lon, lat = pos[0], pos[1]
                if not (-180.0 <= lon <= 180.0):
                    raise ValueError(f"Polygon longitude out of bounds [-180, 180]: {lon}")
                if not (-90.0 <= lat <= 90.0):
                    raise ValueError(f"Polygon latitude out of bounds [-90, 90]: {lat}")
            if ring[0] != ring[-1]:
                raise ValueError(
                    f"GeoJSON Polygon ring {ring_idx} must be closed (first position {ring[0]} != last position {ring[-1]})."
                )
        return rings


class SimulationBanner(BaseModel):
    """Explicit banner attached to responses to prevent mock data from being mistaken for NASA observations."""

    data_origin: DataOrigin = Field(default=DataOrigin.SIMULATED)
    is_simulated: bool = Field(default=True)
    disclaimer: str = Field(
        default=(
            "SIMULATED / MOCK DATA ONLY: Provisional structural data for LUNA NAV backend integration. "
            "Not derived from validated NASA LRO/LOLA observations or final team scientific algorithms."
        )
    )
    pending_specifications: List[str] = Field(
        default_factory=lambda: [
            "Person 1 (Frontend & 3D Visualization)",
            "Person 2 (Terrain Analysis & GIS)",
            "Person 3 (Astronomy & Orbital Mechanics)",
            "Person 4 (Decision Engine & Optimization)",
        ]
    )
    extra_metadata: Optional[Dict[str, Any]] = Field(default=None)
