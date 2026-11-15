"""Pydantic v2 request and response schemas for the LunaNav Scenario Flow (README §6).

Matches the exact JSON contracts produced by P3 (`lunanav.astro`), P4 (`lunanav.decision`),
and P2 (`lunanav.terrain`), and consumed by P1 (`frontend/src/api/types.ts`).
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class CustomSiteInput(BaseModel):
    """Custom lunar coordinates typed by a user."""

    model_config = ConfigDict(extra="allow")

    lat_deg: float = Field(..., description="Planetocentric latitude in degrees (-90..90)")
    lon_deg: float = Field(..., description="East-positive longitude in degrees (-180..180)")
    name: Optional[str] = Field(default=None, description="Optional display name for custom site")
    elevation_m: Optional[float] = Field(
        default=None, description="Optional metres above the 1737.4 km reference sphere"
    )


# A site can be a catalog ID string (e.g. "connecting-ridge", "im-1") or a custom coordinate object
SiteInputType = Union[str, CustomSiteInput, Dict[str, Any]]


class ConditionsRequest(BaseModel):
    """Request body for `POST /api/scenarios/conditions` (Screen 2: Site View)."""

    model_config = ConfigDict(extra="allow")

    site: Any = Field(..., description="Catalog site ID or custom {lat_deg, lon_deg, name?, elevation_m?}")
    start_utc: str = Field(..., description="Landing epoch in ISO-8601 UTC (e.g. 2027-01-10T00:00:00Z)")
    window_days: Optional[float] = Field(
        default=None, description="Analysis window in days (default: 1 synodic month = 29.530589 d)"
    )
    step_h: float = Field(default=0.5, description="Sampling interval in hours")
    thresholds: Optional[Dict[str, float]] = Field(
        default=None, description="Optional custom verdict thresholds (P4)"
    )


class TimelineRequest(BaseModel):
    """Request body for `POST /api/scenarios/timeline` (Screen 3: Timeline)."""

    model_config = ConfigDict(extra="allow")

    site: Any = Field(..., description="Catalog site ID or custom {lat_deg, lon_deg, name?, elevation_m?}")
    start_utc: str = Field(..., description="Landing epoch in ISO-8601 UTC")
    days: Optional[float] = Field(
        default=None, description="Duration in days (default: 29.530589 d)"
    )
    step_h: float = Field(default=1.0, description="Sampling interval in hours")
    thresholds: Optional[Dict[str, float]] = Field(
        default=None, description="Optional custom verdict thresholds (P4)"
    )


class CompareScenarioItem(BaseModel):
    """A single scenario entry inside `CompareRequest`."""

    model_config = ConfigDict(extra="allow")

    site: Any = Field(..., description="Catalog site ID or custom {lat_deg, lon_deg, name?, elevation_m?}")
    start_utc: str = Field(..., description="Landing epoch in ISO-8601 UTC")
    label: Optional[str] = Field(default=None, description="Optional scenario label")
    window_days: Optional[float] = Field(default=None, description="Optional scenario window in days")


class CompareRequest(BaseModel):
    """Request body for `POST /api/scenarios/compare` (Screen 4: Compare + Verdict)."""

    model_config = ConfigDict(extra="allow")

    scenarios: List[Dict[str, Any]] = Field(
        ..., description="List of 1–12 scenario specifications ({site, start_utc, label?, window_days?})"
    )
    window_days: Optional[float] = Field(
        default=None, description="Default analysis window in days when not set per scenario"
    )
    step_h: float = Field(default=1.0, description="Sampling interval in hours")
    thresholds: Optional[Dict[str, float]] = Field(
        default=None, description="Optional custom verdict thresholds (P4)"
    )
    profile: Literal["engineering", "science"] = Field(
        default="engineering", description="Weight profile for P4 multi-criteria ranking"
    )


class DateSweepRequest(BaseModel):
    """Request body for `POST /api/scenarios/date-sweep` (Screen 5: Date Sweep)."""

    model_config = ConfigDict(extra="allow")

    site: Any = Field(..., description="Catalog site ID or custom {lat_deg, lon_deg, name?, elevation_m?}")
    first_start_utc: str = Field(..., description="First landing epoch in ISO-8601 UTC")
    n: int = Field(default=12, description="Number of consecutive lunar dates to sweep (1..36)")
    every_days: Optional[float] = Field(
        default=None, description="Spacing in days between dates (default: 29.530589 d)"
    )
    window_days: Optional[float] = Field(
        default=None, description="Analysis window length per date in days"
    )
    step_h: float = Field(default=1.0, description="Sampling interval in hours")
    thresholds: Optional[Dict[str, float]] = Field(
        default=None, description="Optional custom verdict thresholds (P4)"
    )


class RankScenariosRequest(BaseModel):
    """Request body for `POST /api/scenarios/rank` (P4 WSM/TOPSIS Ranking & Sensitivity)."""

    model_config = ConfigDict(extra="allow")

    rows: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Precomputed scenario rows (each with `label` and `metrics`), or omit if `scenarios` is provided",
    )
    scenarios: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Scenario inputs ({site, start_utc, label?, window_days?}) to compute via P3 and rank via P4",
    )
    window_days: Optional[float] = Field(
        default=None, description="Default analysis window in days when `scenarios` is provided"
    )
    step_h: float = Field(default=1.0, description="Sampling interval in hours when `scenarios` is provided")
    profile: Literal["engineering", "science"] = Field(
        default="engineering", description="Weight profile ('engineering' or 'science')"
    )
    weights: Optional[Dict[str, float]] = Field(
        default=None, description="Optional custom criterion weights"
    )
    method: Literal["wsm", "topsis", "both"] = Field(
        default="both", description="Multi-criteria ranking method"
    )
    include_sensitivity: bool = Field(
        default=True, description="Whether to run Monte-Carlo and OAT weight sensitivity analysis"
    )


class ExportRequest(BaseModel):
    """Request body for `POST /api/export` (CSV / JSON export of scenario comparison)."""

    model_config = ConfigDict(extra="allow")

    format: Literal["csv", "json"] = Field(default="csv", description="Export format ('csv' or 'json')")
    compare_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Existing Compare response object to export directly"
    )
    scenarios: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Scenario inputs to compute and export if `compare_data` is omitted"
    )
    thresholds: Optional[Dict[str, float]] = Field(default=None)


class ExplainerItem(BaseModel):
    """A public educational explainer authored by P4 (`docs/explainers/*.md`)."""

    id: str
    title: str
    markdown: str


class ExplainersResponse(BaseModel):
    """Response schema for `GET /api/explainers`."""

    status: str = "ok"
    count: int
    explainers: List[ExplainerItem]
