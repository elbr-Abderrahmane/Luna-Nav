"""Tests for Layer 4 (Landing Points Evaluation & PDF Report Generation)."""

from fastapi.testclient import TestClient


def test_list_and_evaluate_landing_points(client: TestClient) -> None:
    """Verify GET /api/zones/{zone_id}/points and POST /api/points/evaluate."""
    list_resp = client.get("/api/zones/zone-shackleton-alpha/points")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["zone_id"] == "zone-shackleton-alpha"
    assert list_data["count"] >= 3
    assert list_data["recommended_point_id"] == "pt-shackleton-a1"

    # Evaluate points in zone-shackleton-alpha
    eval_resp = client.post(
        "/api/points/evaluate",
        json={"zone_id": "zone-shackleton-alpha"},
    )
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert eval_data["recommended_point_id"] == "pt-shackleton-a1"
    assert eval_data["data_origin"] == "SIMULATED"
    assert len(eval_data["evaluated_points"]) >= 3

    # Check that pt-shackleton-a2 preserves nearest_obstacle_distance as UNAVAILABLE (null)
    a2_eval = next(
        p for p in eval_data["evaluated_points"] if p["point_id"] == "pt-shackleton-a2"
    )
    assert "nearest_obstacle_distance" in a2_eval["unavailable_metrics"]
    assert a2_eval["point"]["metrics"]["nearest_obstacle_distance"]["value"] is None


def test_evaluate_points_with_custom_coordinates(client: TestClient) -> None:
    """Verify POST /api/points/evaluate supports inspecting custom coordinates."""
    resp = client.post(
        "/api/points/evaluate",
        json={
            "zone_id": "zone-shackleton-alpha",
            "custom_coordinates": {"latitude": -89.58, "longitude": 118.25},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert any(p["point_id"].startswith("pt-custom-") for p in data["evaluated_points"])


def test_generate_and_fetch_pdf_report(client: TestClient) -> None:
    """Verify POST /api/reports/generate and GET /api/reports/{report_id} (JSON & PDF)."""
    gen_resp = client.post(
        "/api/reports/generate",
        json={
            "region_id": "reg-shackleton-rim",
            "compared_zone_ids": [
                "zone-shackleton-alpha",
                "zone-shackleton-beta",
                "zone-shackleton-gamma",
            ],
        },
    )
    assert gen_resp.status_code == 201
    report_meta = gen_resp.json()
    report_id = report_meta["report_id"]
    assert report_id.startswith("rep-")
    assert report_meta["data_origin"] == "SIMULATED"
    assert report_meta["file_size_bytes"] > 100
    assert report_meta["recommended_zone_id"] == "zone-shackleton-alpha"
    assert report_meta["recommended_point_id"] == "pt-shackleton-a1"

    # Fetch JSON metadata
    meta_resp = client.get(f"/api/reports/{report_id}")
    assert meta_resp.status_code == 200
    assert meta_resp.json()["report_id"] == report_id

    # Download binary PDF file
    pdf_resp = client.get(f"/api/reports/{report_id}?format=pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF-")
