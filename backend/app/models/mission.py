"""Pydantic models for Layer 1: Mission Configuration & Earth-Moon Interception.

Provisional schemas awaiting Person 1 (Frontend) and Person 3 (Astronomy & Orbital Mechanics)
specifications. All trajectory and orbital fields are marked SIMULATED.
"""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.common import DataOrigin, Measurement, SimulationBanner


class MissionConfigureRequest(BaseModel):
    """Request payload for POST /api/mission/configure."""

    mission_name: str = Field(
        default="LUNA-NAV-SOUTH-POLE-1",
        min_length=2,
        max_length=120,
        description="Human-readable identifier or codename for the mission.",
    )
    target_arrival_utc: datetime = Field(
        ...,
        description="Expected lunar arrival date and time in ISO-8601 format (UTC).",
    )
    launch_window_Cleanup_flexibility_hours: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=720.0,
        description="Optional flexibility window around target arrival in hours.",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional user notes for mission configuration.",
    )

    @field_validator("target_arrival_utc")
    @classmethod
    def ensure_timezone_aware(cls, dt: datetime) -> datetime:
        """Normalize naive ISO-8601 datetimes to UTC so downstream astronomy adapters get consistent UTC."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)


class InterceptionWindow(BaseModel):
    """Simulated Earth-Moon interception time window."""

    window_start_utc: datetime
    window_end_utc: datetime
    estimated_launch_utc: datetime
    confirmed_arrival_utc: datetime

    @model_validator(mode="after")
    def validate_chronological_order(self) -> "InterceptionWindow":
        if self.window_end_utc < self.window_start_utc:
            raise ValueError("Interception window_end_utc must not precede window_start_utc.")
        if self.confirmed_arrival_utc <= self.estimated_launch_utc:
            raise ValueError("confirmed_arrival_utc must be after estimated_launch_utc.")
        return self


class TrajectoryWaypoint3D(BaseModel):
    """Provisional 3D waypoint for Frontend visualization of Earth-Moon transfer trajectory.

    Coordinate frame awaits confirmation from Person 1 & Person 3 (e.g., ECI / Earth-Moon rotating frame).
    """

    step_index: int = Field(..., ge=0)
    timestamp_utc: datetime
    position_km: List[float] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Provisional [x, y, z] coordinates in kilometers (SIMULATED).",
    )


class OrbitalParametersSummary(BaseModel):
    """Provisional astronomical and transfer parameters (Layer 1 collapsible panel)."""

    earth_moon_distance: Measurement = Field(
        ..., description="Simulated Earth-Moon center-to-center distance at arrival (km)."
    )
    estimated_transfer_duration: Measurement = Field(
        ..., description="Simulated transfer duration from trans-lunar injection to lunar arrival (hours)."
    )
    solar_sub_longitude: Measurement = Field(
        ..., description="Simulated sub-solar selenographic longitude at arrival (deg) — may be UNAVAILABLE."
    )
    earth_sub_latitude: Measurement = Field(
        ..., description="Simulated sub-Earth selenographic latitude at arrival (deg) — may be UNAVAILABLE."
    )
    coordinate_frame_provisional: str = Field(
        default="PROVISIONAL_EARTH_CENTERED_INERTIAL_MOCK",
        description="Placeholder frame name until Person 3 confirms ephemeris standard.",
    )


class MissionResponse(BaseModel):
    """Response model for configured mission and Earth-Moon interception details."""

    mission_id: str = Field(..., min_length=3, description="Unique mission configuration identifier.")
    mission_name: str = Field(..., min_length=2)
    status: str = Field(default="CONFIGURED_SIMULATED")
    data_origin: DataOrigin = Field(default=DataOrigin.SIMULATED)
    created_at_utc: datetime
    interception_window: InterceptionWindow
    orbital_parameters: OrbitalParametersSummary
    trajectory_waypoints: List[TrajectoryWaypoint3D] = Field(
        default_factory=list,
        description="Provisional 3D transfer curve points for Layer 1 scene visualization.",
    )
    notes: Optional[str] = None
    simulation_banner: SimulationBanner = Field(default_factory=SimulationBanner)
