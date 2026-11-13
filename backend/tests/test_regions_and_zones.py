"""Tests for Layer 2 (Regions) and Layer 3 (Landing Zones & 3-Zone Comparison)."""

from fastapi.testclient import TestClient


def test_list_and_get_regions(client: TestClient) -> None:
    """Verify GET /api/regions and GET /api/regions/{region_id}."""
    list_resp = client.get("/api/regions")
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["count"] >= 3
    assert body["simulation_banner"]["is_simulated"] is True

    first_region_id = body["regions"][0]["region_id"]
    detail_resp = client.get(f"/api/regions/{first_region_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["region"]["region_id"] == first_region_id
    assert detail["region"]["boundary_geojson"]["type"] == "Polygon"


def test_get_unknown_region_returns_404(client: TestClient) -> None:
    """Verify unknown region_id returns 404."""
    resp = client.get("/api/regions/reg-nonexistent")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_list_zones_for_region(client: TestClient) -> None:
    """Verify GET /api/regions/{region_id}/zones returns valid polygons and metrics."""
    resp = client.get("/api/regions/reg-shackleton-rim/zones")
    assert resp.status_code == 200
    data = resp.json()
    assert data["region_id"] == "reg-shackleton-rim"
    assert data["count"] >= 3

    # Verify zone-shackleton-beta explicitly marks boulder_density as UNAVAILABLE (null), not 0
    beta_zone = next(z for z in data["zones"] if z["zone_id"] == "zone-shackleton-beta")
    boulder = beta_zone["parameters"]["boulder_density"]
    assert boulder["status"] == "UNAVAILABLE"
    assert boulder["value"] is None


def test_three_zone_comparison_success(client: TestClient) -> None:
    """Verify POST /api/zones/compare ranks exactly three candidate zones."""
    payload = {
        "region_id": "reg-shackleton-rim",
        "zone_ids": [
            "zone-shackleton-beta",
            "zone-shackleton-alpha",
            "zone-shackleton-gamma",
        ],
    }
    resp = client.post("/api/zones/compare", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["recommended_zone_id"] == "zone-shackleton-alpha"
    assert len(data["ranked_candidates"]) == 3
    assert [c["rank"] for c in data["ranked_candidates"]] == [1, 2, 3]

    # Verify unavailable metrics are tracked on zone-shackleton-beta
    beta_ranked = next(
        c for c in data["ranked_candidates"] if c["zone_id"] == "zone-shackleton-beta"
    )
    assert "boulder_density" in beta_ranked["unavailable_metrics"]


def test_invalid_zone_selections_rejected(client: TestClient) -> None:
    """Verify fewer than 3, more than 3, duplicate, or cross-region zones fail validation."""
    # Case 1: Only 2 zones provided
    resp_two = client.post(
        "/api/zones/compare",
        json={"zone_ids": ["zone-shackleton-alpha", "zone-shackleton-beta"]},
    )
    assert resp_two.status_code == 422

    # Case 2: 4 zones provided
    resp_four = client.post(
        "/api/zones/compare",
        json={
            "zone_ids": [
                "zone-shackleton-alpha",
                "zone-shackleton-beta",
                "zone-shackleton-gamma",
                "zone-shackleton-delta",
            ]
        },
    )
    assert resp_four.status_code == 422

    # Case 3: 3 zones with duplicates
    resp_dup = client.post(
        "/api/zones/compare",
        json={
            "zone_ids": [
                "zone-shackleton-alpha",
                "zone-shackleton-alpha",
                "zone-shackleton-beta",
            ]
        },
    )
    assert resp_dup.status_code == 422

    # Case 4: Cross-region zones (mixing Shackleton and Malapert)
    resp_cross = client.post(
        "/api/zones/compare",
        json={
            "zone_ids": [
                "zone-shackleton-alpha",
                "zone-shackleton-beta",
                "zone-malapert-alpha",
            ]
        },
    )
    assert resp_cross.status_code == 422
    assert resp_cross.json()["error"]["code"] == "CROSS_REGION_ZONE_COMPARISON_INVALID"
