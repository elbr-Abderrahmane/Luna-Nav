"""Decision Service for Layer 3 (Zone Comparison) & Layer 4 (Point Evaluation).

Orchestrates domain validation (existence of zones/points/missions, region membership)
and delegates ranking to `BaseDecisionAdapter` (Person 4's integration boundary).
"""

import logging
import uuid
from typing import List, Optional

from app.core.exceptions import DomainValidationError, ResourceNotFoundError
from app.integrations.decision_adapter import BaseDecisionAdapter, get_decision_adapter
from app.models.common import (
    DataOrigin,
    GeoJSONPointGeometry,
    Measurement,
    MeasurementStatus,
)
from app.models.point import (
    LandingPointModel,
    PointEngineeringMetrics,
    PointEvaluateRequest,
    PointEvaluationResponse,
)
from app.models.zone import (
    LandingZoneModel,
    ZoneComparisonRequest,
    ZoneComparisonResponse,
)
from app.services.mission_service import MissionService
from app.services.terrain_service import TerrainService

logger = logging.getLogger("luna_nav.services.decision")


class DecisionService:
    """Business service coordinating Layer 3 zone comparison and Layer 4 point evaluation."""

    def __init__(
        self,
        decision_adapter: Optional[BaseDecisionAdapter] = None,
        terrain_service: Optional[TerrainService] = None,
        mission_service: Optional[MissionService] = None,
    ) -> None:
        self.decision_adapter = decision_adapter or get_decision_adapter()
        self.terrain_service = terrain_service or TerrainService()
        self.mission_service = mission_service or MissionService()

    def compare_three_zones(self, request: ZoneComparisonRequest) -> ZoneComparisonResponse:
        """Validate and compare exactly three candidate landing zones."""
        if request.mission_id:
            self.mission_service.get_mission(request.mission_id)

        if request.region_id:
            self.terrain_service.get_region_by_id(request.region_id)

        zones: List[LandingZoneModel] = []
        for zid in request.zone_ids:
            zone = self.terrain_service.get_zone_by_id(zid)
            if request.region_id and zone.region_id != request.region_id:
                raise DomainValidationError(
                    message=(
                        f"Landing zone '{zid}' belongs to region '{zone.region_id}', "
                        f"not the requested region '{request.region_id}'."
                    ),
                    error_code="ZONE_REGION_MISMATCH",
                    details={
                        "zone_id": zid,
                        "zone_region_id": zone.region_id,
                        "expected_region_id": request.region_id,
                    },
                )
            zones.append(zone)

        # Ensure all 3 zones belong to the same region even when region_id was omitted
        distinct_regions = {z.region_id for z in zones}
        if len(distinct_regions) > 1:
            raise DomainValidationError(
                message=(
                    "All three compared landing zones must belong to the same South Pole region. "
                    f"Found multiple regions: {sorted(distinct_regions)}."
                ),
                error_code="CROSS_REGION_ZONE_COMPARISON_INVALID",
                details={"regions_found": sorted(distinct_regions)},
            )

        inferred_region_id = request.region_id or zones[0].region_id
        ranked_candidates = self.decision_adapter.evaluate_three_zones(
            zones=zones, mission_id=request.mission_id
        )
        winner = ranked_candidates[0]

        comparison_id = f"cmp-{uuid.uuid4().hex[:8]}"
        summary = (
            f"SIMULATED COMPARISON SUMMARY: Among the 3 evaluated zones in region "
            f"'{inferred_region_id}', '{winner.zone_name}' ({winner.zone_id}) achieved Rank #1 "
            f"with a provisional mock score of {winner.simulated_suitability_score.value} "
            f"({winner.simulated_suitability_score.unit}). "
            "Unavailable scientific metrics were preserved as null and excluded from zero-imputation."
        )

        return ZoneComparisonResponse(
            comparison_id=comparison_id,
            mission_id=request.mission_id,
            region_id=inferred_region_id,
            data_origin=DataOrigin.SIMULATED,
            recommended_zone_id=winner.zone_id,
            comparison_summary=summary,
            ranked_candidates=ranked_candidates,
        )

    def evaluate_points(self, request: PointEvaluateRequest) -> PointEvaluationResponse:
        """Evaluate candidate landing points inside a landing zone and recommend optimal coordinates."""
        zone = self.terrain_service.get_zone_by_id(request.zone_id)
        if request.mission_id:
            self.mission_service.get_mission(request.mission_id)

        point_list_resp = self.terrain_service.get_points_for_zone(request.zone_id)
        available_points: List[LandingPointModel] = list(point_list_resp.points)

        # If a zone has no predefined points in points.json, synthesize a clearly marked
        # SIMULATED centroid marker so any valid zone can still be evaluated in Layer 4.
        if not available_points and not request.custom_coordinates and not request.point_ids:
            available_points.append(self._build_simulated_point_from_zone(zone))

        if request.point_ids is not None:
            points_by_id = {pt.point_id: pt for pt in available_points}
            selected_points: List[LandingPointModel] = []
            for pid in request.point_ids:
                if pid not in points_by_id:
                    raise ResourceNotFoundError(
                        resource_type="LandingPoint",
                        resource_id=pid,
                        details={"zone_id": request.zone_id},
                    )
                selected_points.append(points_by_id[pid])
            available_points = selected_points

        if request.custom_coordinates is not None:
            custom_pt = self._build_custom_simulated_point(zone, request)
            available_points.append(custom_pt)

        evaluated = self.decision_adapter.evaluate_landing_points(
            points=available_points,
            mission_id=request.mission_id,
        )
        winner = evaluated[0]

        evaluation_id = f"eval-{uuid.uuid4().hex[:8]}"
        summary = (
            f"SIMULATED POINT EVALUATION: '{winner.point_name}' ({winner.point_id}) at "
            f"({winner.point.coordinates.latitude:.4f} deg, {winner.point.coordinates.longitude:.4f} deg) "
            f"is recommended in zone '{request.zone_id}' with provisional score "
            f"{winner.simulated_suitability_score.value}."
        )

        return PointEvaluationResponse(
            evaluation_id=evaluation_id,
            zone_id=request.zone_id,
            mission_id=request.mission_id,
            data_origin=DataOrigin.SIMULATED,
            recommended_point_id=winner.point_id,
            recommended_coordinates=winner.point.coordinates,
            recommendation_summary=summary,
            evaluated_points=evaluated,
        )

    @staticmethod
    def _build_simulated_point_from_zone(zone: LandingZoneModel) -> LandingPointModel:
        elev = (
            zone.centroid.elevation_m.value
            if zone.centroid.elevation_m and zone.centroid.elevation_m.value is not None
            else 2000.0
        )
        return LandingPointModel(
            point_id=f"pt-{zone.zone_id}-centroid-mock",
            zone_id=zone.zone_id,
            name=f"{zone.name} Centroid Marker (MOCK)",
            data_origin=DataOrigin.SIMULATED,
            coordinates=zone.centroid,
            point_geojson=GeoJSONPointGeometry(
                type="Point",
                coordinates=[zone.centroid.longitude, zone.centroid.latitude, elev],
            ),
            metrics=PointEngineeringMetrics(
                local_slope=zone.parameters.average_slope,
                surface_roughness=zone.parameters.surface_roughness,
                elevation=zone.parameters.elevation,
                nearest_crater_distance=Measurement(
                    value=120.0,
                    unit="m",
                    status=MeasurementStatus.SIMULATED,
                    note="MOCK centroid crater clearance",
                ),
                nearest_obstacle_distance=Measurement(
                    value=None,
                    unit="m",
                    status=MeasurementStatus.UNAVAILABLE,
                    note="UNAVAILABLE: Sub-meter obstacle distance not mapped.",
                ),
                local_illumination=zone.parameters.illumination_percentage,
                earth_visibility=zone.parameters.earth_visibility_percentage,
            ),
            is_provisional_optimal=True,
        )

    @staticmethod
    def _build_custom_simulated_point(
        zone: LandingZoneModel, request: PointEvaluateRequest
    ) -> LandingPointModel:
        coords = request.custom_coordinates
        assert coords is not None
        elev_val = (
            coords.elevation_m.value
            if coords.elevation_m and coords.elevation_m.value is not None
            else 2100.0
        )
        return LandingPointModel(
            point_id=f"pt-custom-{uuid.uuid4().hex[:6]}",
            zone_id=zone.zone_id,
            name="Custom Inspected Coordinates (SIMULATED)",
            data_origin=DataOrigin.SIMULATED,
            coordinates=coords,
            point_geojson=GeoJSONPointGeometry(
                type="Point",
                coordinates=[coords.longitude, coords.latitude, elev_val],
            ),
            metrics=PointEngineeringMetrics(
                local_slope=Measurement(
                    value=4.5,
                    unit="deg",
                    status=MeasurementStatus.SIMULATED,
                    note="SIMULATED local slope at custom coordinates",
                ),
                surface_roughness=Measurement(
                    value=0.40,
                    unit="m",
                    status=MeasurementStatus.SIMULATED,
                    note="SIMULATED roughness at custom coordinates",
                ),
                elevation=Measurement(
                    value=elev_val,
                    unit="m",
                    status=MeasurementStatus.SIMULATED,
                    note="SIMULATED elevation at custom coordinates",
                ),
                nearest_crater_distance=Measurement(
                    value=105.0,
                    unit="m",
                    status=MeasurementStatus.SIMULATED,
                    note="SIMULATED crater distance",
                ),
                nearest_obstacle_distance=Measurement(
                    value=None,
                    unit="m",
                    status=MeasurementStatus.UNAVAILABLE,
                    note="UNAVAILABLE: Custom coordinate obstacle clearance pending Person 2 module.",
                ),
                local_illumination=Measurement(
                    value=82.0,
                    unit="%",
                    status=MeasurementStatus.SIMULATED,
                    note="SIMULATED illumination",
                ),
                earth_visibility=Measurement(
                    value=78.0,
                    unit="%",
                    status=MeasurementStatus.SIMULATED,
                    note="SIMULATED Earth visibility",
                ),
            ),
            is_provisional_optimal=False,
        )
