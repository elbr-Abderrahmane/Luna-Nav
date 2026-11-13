"""Tests for Missing Data Handling, GeoJSON/Coordinate Validation, and Adapter Interfaces."""

import pytest
from pydantic import ValidationError

from app.core.exceptions import AdapterIntegrationError
from app.integrations.astronomy_adapter import RealAstronomyAdapterStub
from app.integrations.decision_adapter import RealDecisionAdapterStub
from app.integrations.terrain_adapter import RealTerrainAdapterStub
from app.models.common import (
    GeoJSONPolygonGeometry,
    LunarCoordinates,
    Measurement,
    MeasurementStatus,
)


def test_missing_data_handling_never_treated_as_zero() -> None:
    """Verify missing scientific measurements are explicitly UNAVAILABLE with value=None."""
    # Passing value=None automatically sets status to UNAVAILABLE and preserves value=None
    m = Measurement(value=None, unit="boulders/km^2")
    assert m.value is None
    assert m.status == MeasurementStatus.UNAVAILABLE

    # Passing status=UNAVAILABLE with a numeric value (including 0.0) must raise a ValidationError
    with pytest.raises(ValidationError):
        Measurement(value=0.0, unit="boulders/km^2", status=MeasurementStatus.UNAVAILABLE)


def test_coordinate_and_geojson_validation() -> None:
    """Verify out-of-range lunar coordinates and unclosed polygons are rejected."""
    with pytest.raises(ValidationError):
        LunarCoordinates(latitude=-95.0, longitude=120.0)

    with pytest.raises(ValidationError):
        LunarCoordinates(latitude=-89.0, longitude=195.0)

    # Unclosed polygon ring (first != last position) must fail
    with pytest.raises(ValidationError):
        GeoJSONPolygonGeometry(
            type="Polygon",
            coordinates=[[[115.0, -89.4], [125.0, -89.4], [125.0, -89.8], [115.0, -89.9]]],
        )


def test_real_adapter_stubs_raise_integration_error_until_connected() -> None:
    """Verify Real*AdapterStub classes fail explicitly with AdapterIntegrationError."""
    terrain_stub = RealTerrainAdapterStub()
    with pytest.raises(AdapterIntegrationError):
        terrain_stub.fetch_south_pole_regions()

    astronomy_stub = RealAstronomyAdapterStub()
    with pytest.raises(AdapterIntegrationError):
        from datetime import datetime, timezone

        astronomy_stub.calculate_mission_interception(datetime.now(timezone.utc))

    decision_stub = RealDecisionAdapterStub()
    with pytest.raises(AdapterIntegrationError):
        decision_stub.evaluate_three_zones([])
