"""Tests for API Health and Layer 1 (Mission Configuration & Interception)."""

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    """Verify GET /health returns status ok and adapter statuses."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["data_origin"] == "MOCK_AND_SIMULATED"
    assert data["adapters"]["terrain_gis_person_2"] == "MOCK"
    assert data["adapters"]["astronomy_orbital_person_3"] == "MOCK"
    assert data["adapters"]["decision_engine_person_4"] == "MOCK"


def test_configure_and_retrieve_mission(client: TestClient) -> None:
    """Verify POST /api/mission/configure and GET /api/mission/{mission_id}."""
    payload = {
        "mission_name": "ARTEMIS-SCOUT-TEST",
        "target_arrival_utc": "2027-08-21T16:30:00Z",
        "notes": "Test mission configuration",
    }
    post_resp = client.post("/api/mission/configure", json=payload)
    assert post_resp.status_code == 201
    mission = post_resp.json()

    assert mission["mission_id"].startswith("msn-")
    assert mission["mission_name"] == "ARTEMIS-SCOUT-TEST"
    assert mission["data_origin"] == "SIMULATED"
    assert mission["simulation_banner"]["is_simulated"] is True
    assert len(mission["trajectory_waypoints"]) >= 3

    # Verify missing astronomical parameter (solar_sub_longitude) is explicitly UNAVAILABLE (null), not 0
    solar_lon = mission["orbital_parameters"]["solar_sub_longitude"]
    assert solar_lon["status"] == "UNAVAILABLE"
    assert solar_lon["value"] is None

    # Retrieve configured mission via GET /api/mission/{mission_id}
    get_resp = client.get(f"/api/mission/{mission['mission_id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["mission_id"] == mission["mission_id"]


def test_mission_validation_invalid_datetime(client: TestClient) -> None:
    """Verify invalid date/time strings are rejected with 422 validation error."""
    bad_payload = {
        "mission_name": "INVALID-DATE-MISSION",
        "target_arrival_utc": "not-a-valid-iso-date",
    }
    resp = client.post("/api/mission/configure", json=bad_payload)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "REQUEST_VALIDATION_ERROR"


def test_get_unknown_mission_returns_404(client: TestClient) -> None:
    """Verify requesting a non-existent mission_id returns 404 RESOURCE_NOT_FOUND."""
    resp = client.get("/api/mission/msn-does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
