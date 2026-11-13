"""Provisional Integration Adapter for Person 4 (Decision Engine & Optimization).

PROVISIONAL INTERFACE — Awaiting Person 4's Technical Specification README.
IMPORTANT RESTRICTION: Do NOT invent scientific landing-site scoring weights or
multi-criteria optimization algorithms here.
`MockDecisionAdapter` provides deterministic, mock placeholder rankings and explicitly
tracks `UNAVAILABLE` metrics without treating missing data as zero.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from app.core.config import settings
from app.core.exceptions import AdapterIntegrationError
from app.models.common import Measurement, MeasurementStatus
from app.models.point import EvaluatedPointCandidate, LandingPointModel
from app.models.zone import LandingZoneModel, RankedZoneCandidate

logger = logging.getLogger("luna_nav.integrations.decision")

# Static lookup table of mock placeholder scores by zone_id / point_id so we NEVER invent
# scientific scoring weights while still returning deterministic, testable structural rankings.
MOCK_ZONE_PLACEHOLDER_SCORES: Dict[str, float] = {
    "zone-shackleton-alpha": 91.0,
    "zone-shackleton-delta": 85.0,
    "zone-shackleton-beta": 82.0,
    "zone-shackleton-gamma": 71.0,
    "zone-degerlache-alpha": 87.0,
    "zone-degerlache-beta": 79.0,
    "zone-degerlache-gamma": 72.0,
    "zone-malapert-alpha": 89.0,
    "zone-malapert-beta": 80.0,
    "zone-malapert-gamma": 73.0,
}

MOCK_POINT_PLACEHOLDER_SCORES: Dict[str, float] = {
    "pt-shackleton-a1": 94.0,
    "pt-shackleton-a2": 84.0,
    "pt-shackleton-a3": 76.0,
    "pt-shackleton-b1": 86.0,
    "pt-shackleton-g1": 78.0,
}


class BaseDecisionAdapter(ABC):
    """PROVISIONAL INTERFACE for Person 4's Decision Engine & Optimization module.

    Covers:
    1. Landing-zone evaluation (comparing 3 candidate zones and recommending the best).
    2. Landing-point evaluation (ranking candidate points within a zone and recommending the optimal coordinates).
    """

    @abstractmethod
    def evaluate_three_zones(
        self, zones: List[LandingZoneModel], mission_id: Optional[str] = None
    ) -> List[RankedZoneCandidate]:
        """Compare exactly three candidate landing zones and return ranked candidates."""

    @abstractmethod
    def evaluate_landing_points(
        self, points: List[LandingPointModel], mission_id: Optional[str] = None
    ) -> List[EvaluatedPointCandidate]:
        """Evaluate candidate landing points inside a zone and return ranked candidates."""


class MockDecisionAdapter(BaseDecisionAdapter):
    """Mock implementation using deterministic placeholder lookup values (not invented scoring weights)."""

    @staticmethod
    def _collect_unavailable_zone_metrics(zone: LandingZoneModel) -> List[str]:
        """Identify any zone parameters marked UNAVAILABLE so they are reported rather than zero-imputed."""
        unavailable: List[str] = []
        params = zone.parameters
        for field_name in (
            "average_slope",
            "max_slope",
            "surface_roughness",
            "elevation",
            "crater_density",
            "boulder_density",
            "illumination_percentage",
            "earth_visibility_percentage",
        ):
            measurement: Measurement = getattr(params, field_name)
            if measurement.status == MeasurementStatus.UNAVAILABLE or measurement.value is None:
                unavailable.append(field_name)
        return unavailable

    @staticmethod
    def _collect_unavailable_point_metrics(point: LandingPointModel) -> List[str]:
        """Identify any point metrics marked UNAVAILABLE so they are reported rather than zero-imputed."""
        unavailable: List[str] = []
        metrics = point.metrics
        for field_name in (
            "local_slope",
            "surface_roughness",
            "elevation",
            "nearest_crater_distance",
            "nearest_obstacle_distance",
            "local_illumination",
            "earth_visibility",
        ):
            measurement: Measurement = getattr(metrics, field_name)
            if measurement.status == MeasurementStatus.UNAVAILABLE or measurement.value is None:
                unavailable.append(field_name)
        return unavailable

    def evaluate_three_zones(
        self, zones: List[LandingZoneModel], mission_id: Optional[str] = None
    ) -> List[RankedZoneCandidate]:
        logger.debug(
            "MockDecisionAdapter: comparing %d zones (mission_id=%s)",
            len(zones),
            mission_id,
        )
        # Sort deterministically by static mock lookup score descending
        sorted_zones = sorted(
            zones,
            key=lambda z: MOCK_ZONE_PLACEHOLDER_SCORES.get(z.zone_id, 75.0),
            reverse=True,
        )

        ranked_results: List[RankedZoneCandidate] = []
        for idx, zone in enumerate(sorted_zones, start=1):
            placeholder_score = MOCK_ZONE_PLACEHOLDER_SCORES.get(zone.zone_id, 75.0)
            unavailable_metrics = self._collect_unavailable_zone_metrics(zone)
            unavailable_note = (
                f" Unavailable metrics explicitly excluded (not treated as 0): {', '.join(unavailable_metrics)}."
                if unavailable_metrics
                else " All mock parameters present."
            )
            ranked_results.append(
                RankedZoneCandidate(
                    zone_id=zone.zone_id,
                    zone_name=zone.name,
                    rank=idx,
                    simulated_suitability_score=Measurement(
                        value=placeholder_score,
                        unit="score_0_100_mock",
                        status=MeasurementStatus.SIMULATED,
                        note="MOCK placeholder ranking score; awaiting Person 4 decision engine weights.",
                    ),
                    eligible=True,
                    unavailable_metrics=unavailable_metrics,
                    rationale_simulated=(
                        f"SIMULATED Rank #{idx} for {zone.name} using provisional mock lookup "
                        f"(score={placeholder_score}).{unavailable_note}"
                    ),
                    zone_details=zone,
                )
            )
        return ranked_results

    def evaluate_landing_points(
        self, points: List[LandingPointModel], mission_id: Optional[str] = None
    ) -> List[EvaluatedPointCandidate]:
        logger.debug(
            "MockDecisionAdapter: evaluating %d points (mission_id=%s)",
            len(points),
            mission_id,
        )
        sorted_points = sorted(
            points,
            key=lambda p: (
                1 if p.is_provisional_optimal else 0,
                MOCK_POINT_PLACEHOLDER_SCORES.get(p.point_id, 75.0),
            ),
            reverse=True,
        )

        evaluated: List[EvaluatedPointCandidate] = []
        for idx, pt in enumerate(sorted_points, start=1):
            placeholder_score = MOCK_POINT_PLACEHOLDER_SCORES.get(pt.point_id, 75.0)
            unavailable_metrics = self._collect_unavailable_point_metrics(pt)
            unavailable_note = (
                f" Unavailable metrics kept as null (not 0): {', '.join(unavailable_metrics)}."
                if unavailable_metrics
                else " Complete mock metric set."
            )
            evaluated.append(
                EvaluatedPointCandidate(
                    point_id=pt.point_id,
                    point_name=pt.name,
                    rank=idx,
                    simulated_suitability_score=Measurement(
                        value=placeholder_score,
                        unit="score_0_100_mock",
                        status=MeasurementStatus.SIMULATED,
                        note="MOCK placeholder point score; awaiting Person 4 decision engine.",
                    ),
                    passes_engineering_constraints=True,
                    unavailable_metrics=unavailable_metrics,
                    evaluation_notes_simulated=(
                        f"SIMULATED Point Rank #{idx} ({pt.name}).{unavailable_note}"
                    ),
                    point=pt,
                )
            )
        return evaluated


class RealDecisionAdapterStub(BaseDecisionAdapter):
    """Placeholder for Person 4's real Decision Engine & Optimization module."""

    def _not_connected(self, operation: str) -> None:
        raise AdapterIntegrationError(
            adapter_name="RealDecisionAdapterStub (Person 4 - Decision Engine & Optimization)",
            message=(
                f"Operation '{operation}' called with USE_MOCK_DECISION=false, "
                "but Person 4's Decision Engine module has not been wired yet."
            ),
        )

    def evaluate_three_zones(
        self, zones: List[LandingZoneModel], mission_id: Optional[str] = None
    ) -> List[RankedZoneCandidate]:
        self._not_connected("evaluate_three_zones")
        return []

    def evaluate_landing_points(
        self, points: List[LandingPointModel], mission_id: Optional[str] = None
    ) -> List[EvaluatedPointCandidate]:
        self._not_connected("evaluate_landing_points")
        return []


def get_decision_adapter() -> BaseDecisionAdapter:
    """Factory returning either MockDecisionAdapter or RealDecisionAdapterStub."""
    if settings.use_mock_decision:
        return MockDecisionAdapter()
    return RealDecisionAdapterStub()
