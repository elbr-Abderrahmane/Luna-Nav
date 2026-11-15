"""Full-stack integration tests for the unified LunaNav API (P1 + P2 + P3 + P4 + P5).

Verifies that all unified endpoints work end-to-end and adhere to the contracts in
`frontend/src/api/types.ts` and `README.md` §6:
- /api/sites (P3 catalogue)
- /api/scenarios/conditions, /timeline, /compare, /date-sweep, /rank (P3 + P4 + P2)
- /api/terrain/inspect, /coverage, /elevation, /heightmap, /metrics (P2)
- /api/explainers (P4 educational explainers)
- /api/export (CSV & JSON export for P1)
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_api_health_alias(client: TestClient) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


def test_list_and_get_sites(client: TestClient) -> None:
    resp = client.get("/api/sites")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    sites = body["sites"]
    assert isinstance(sites, list)
    assert len(sites) >= 16
    ids = {s["id"] for s in sites}
    assert "connecting-ridge" in ids
    assert "shackleton-rim" in ids
    assert "im-1" in ids

    # Filter by category
    artemis_resp = client.get("/api/sites?category=artemis")
    assert artemis_resp.status_code == 200
    artemis_sites = artemis_resp.json()["sites"]
    assert len(artemis_sites) > 0
    assert all(s["category"] == "artemis" for s in artemis_sites)

    # Single site
    one_resp = client.get("/api/sites/connecting-ridge")
    assert one_resp.status_code == 200
    assert one_resp.json()["site"]["id"] == "connecting-ridge"

    # Unknown site -> 404
    missing_resp = client.get("/api/sites/not-a-real-site")
    assert missing_resp.status_code == 404


def test_scenario_conditions_enriches_verdict_and_terrain(client: TestClient) -> None:
    resp = client.post(
        "/api/scenarios/conditions",
        json={
            "site": "connecting-ridge",
            "start_utc": "2027-01-10T00:00:00Z",
            "window_days": 5.0,
            "step_h": 2.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["site"]["id"] == "connecting-ridge"
    # P3 fields
    assert "sunlight_pct" in data["metrics"]
    assert "earth_visibility_pct" in data["metrics"]
    assert "countdown" in data
    assert "sun" in data["countdown"]
    assert "earth" in data["countdown"]
    # P4 enrichment
    assert "verdict" in data
    assert data["verdict"]["level"] in ("viable", "marginal", "not_viable")
    assert "verdict_explanation" in data
    assert isinstance(data["verdict_explanation"], str) and len(data["verdict_explanation"]) > 10
    # P2 enrichment
    assert "terrain" in data
    assert "coverage" in data["terrain"]


def test_scenario_conditions_custom_coordinates(client: TestClient) -> None:
    resp = client.post(
        "/api/scenarios/conditions",
        json={
            "site": {
                "name": "Custom South Pole",
                "lat_deg": -89.2,
                "lon_deg": -120.0,
            },
            "start_utc": "2027-01-10T00:00:00Z",
            "window_days": 3.0,
            "step_h": 3.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["site"]["name"] == "Custom South Pole"
    assert "verdict" in data


def test_scenario_conditions_invalid_site_returns_422(client: TestClient) -> None:
    resp = client.post(
        "/api/scenarios/conditions",
        json={
            "site": "totally-nonexistent-site-id",
            "start_utc": "2027-01-10T00:00:00Z",
        },
    )
    assert resp.status_code == 422
    data = resp.json()
    assert data["status"] == "error"
    assert "error" in data


def test_scenario_timeline_returns_series_and_verdict(client: TestClient) -> None:
    resp = client.post(
        "/api/scenarios/timeline",
        json={
            "site": "connecting-ridge",
            "start_utc": "2027-01-10T00:00:00Z",
            "days": 3.0,
            "step_h": 3.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "series" in data
    assert len(data["series"]["t_utc"]) > 0
    assert len(data["series"]["sun_elevation_deg"]) == len(data["series"]["t_utc"])
    assert "horizon_profile" in data
    assert len(data["horizon_profile"]["azimuth_deg"]) == 360
    assert "verdict" in data


def test_scenario_compare_enriches_verdicts_ranking_and_explanations(client: TestClient) -> None:
    resp = client.post(
        "/api/scenarios/compare",
        json={
            "scenarios": [
                {"site": "connecting-ridge", "start_utc": "2027-01-10T00:00:00Z"},
                {"site": "shackleton-rim", "start_utc": "2027-01-10T00:00:00Z"},
                {"site": "im-1", "start_utc": "2027-01-10T00:00:00Z"},
            ],
            "window_days": 5.0,
            "step_h": 2.0,
            "profile": "science",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert len(data["rows"]) == 3
    for row in data["rows"]:
        assert "verdict" in row
        assert row["verdict"]["level"] in ("viable", "marginal", "not_viable")
    assert "explanation" in data
    assert isinstance(data["explanation"], str) and len(data["explanation"]) > 10
    assert "ranking" in data
    assert len(data["ranking"]["ranking"]) == 3
    assert "sensitivity" in data


def test_scenario_date_sweep_enriches_verdicts_and_explanation(client: TestClient) -> None:
    resp = client.post(
        "/api/scenarios/date-sweep",
        json={
            "site": "connecting-ridge",
            "first_start_utc": "2027-01-10T00:00:00Z",
            "n": 3,
            "every_days": 10.0,
            "window_days": 4.0,
            "step_h": 3.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert len(data["rows"]) == 3
    for row in data["rows"]:
        assert "verdict" in row
    assert "explanation" in data
    assert "best" in data


def test_scenario_rank_endpoint(client: TestClient) -> None:
    resp = client.post(
        "/api/scenarios/rank",
        json={
            "scenarios": [
                {"site": "connecting-ridge", "start_utc": "2027-01-10T00:00:00Z"},
                {"site": "shackleton-rim", "start_utc": "2027-01-10T00:00:00Z"},
            ],
            "window_days": 4.0,
            "step_h": 3.0,
            "profile": "engineering",
            "include_sensitivity": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["profile"] == "engineering"
    assert len(data["ranking"]) == 2
    assert "explanation" in data
    assert "sensitivity" in data


def test_explainers_endpoints(client: TestClient) -> None:
    list_resp = client.get("/api/explainers")
    assert list_resp.status_code == 200
    items = list_resp.json()["explainers"]
    assert len(items) == 5
    ids = {item["id"] for item in items}
    assert {"sunlight", "earth_visibility", "lunar_day", "lunar_libration", "verdicts"} <= ids

    detail_resp = client.get("/api/explainers/verdicts")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == "verdicts"
    assert "Viable" in detail["markdown"]

    missing_resp = client.get("/api/explainers/nonexistent")
    assert missing_resp.status_code == 404


def test_export_csv_and_json(client: TestClient) -> None:
    scenarios = [
        {"site": "connecting-ridge", "start_utc": "2027-01-10T00:00:00Z"},
        {"site": "shackleton-rim", "start_utc": "2027-01-10T00:00:00Z"},
    ]
    csv_resp = client.post(
        "/api/export",
        json={
            "format": "csv",
            "scenarios": scenarios,
        },
    )
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    csv_text = csv_resp.text
    assert "sunlight_pct" in csv_text
    assert "connecting-ridge" in csv_text

    json_resp = client.post(
        "/api/export",
        json={
            "format": "json",
            "scenarios": scenarios,
        },
    )
    assert json_resp.status_code == 200
    assert "application/json" in json_resp.headers["content-type"]


def test_terrain_endpoints_graceful_response(client: TestClient) -> None:
    inspect_resp = client.get("/api/terrain/inspect")
    assert inspect_resp.status_code == 200
    assert inspect_resp.json()["status"] in ("ok", "dem_unavailable", "error")

    cov_resp = client.get("/api/terrain/coverage?lat_deg=-89.45&lon_deg=-137.04")
    assert cov_resp.status_code == 200
    assert "nominal_coverage" in cov_resp.json()

    el_resp = client.get("/api/terrain/elevation?lat_deg=-89.45&lon_deg=-137.04")
    assert el_resp.status_code == 200
    assert el_resp.json()["status"] in ("ok", "dem_unavailable", "outside_dem", "nodata")

    hm_resp = client.get("/api/terrain/heightmap?lat_deg=-89.45&lon_deg=-137.04&radius_m=800")
    assert hm_resp.status_code == 200
    assert hm_resp.json()["status"] in ("ok", "dem_unavailable", "outside_dem")

    metrics_resp = client.get("/api/terrain/metrics?lat_deg=-89.45&lon_deg=-137.04&radius_m=240")
    assert metrics_resp.status_code == 200
    assert metrics_resp.json()["status"] in ("ok", "dem_unavailable", "outside_dem", "nodata")
