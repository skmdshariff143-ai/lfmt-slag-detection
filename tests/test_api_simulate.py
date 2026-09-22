"""
Integration and unit tests for /api/v1/simulate REST endpoints.
"""

import time
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_get_simulation_backends():
    resp = client.get("/api/v1/simulate/backends")
    assert resp.status_code == 200
    data = resp.json()
    assert "python_fem" in data
    assert "matlab_fdm" in data
    assert data["python_fem"]["status"] == "AVAILABLE"
    assert data["matlab_fdm"]["status"] == "AVAILABLE"


@pytest.mark.matlab
def test_start_simulation_and_get_result():
    payload = {
        "backend": "matlab_fdm",
        "preset": "healthy",
        "duration_s": 0.4,
        "timestep_s": 0.1,
        "camera_sampling_rate_hz": 10.0,
        "spatial_resolution": {"nx": 20, "ny": 14, "nz": 6}
    }
    resp = client.post("/api/v1/simulate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "run_id" in data
    run_id = data["run_id"]

    # Poll status briefly until completed
    for _ in range(30):
        s_resp = client.get(f"/api/v1/simulate/{run_id}")
        assert s_resp.status_code == 200
        s_data = s_resp.json()
        if s_data["status"] == "COMPLETED":
            break
        elif s_data["status"] == "FAILED":
            pytest.fail(f"Simulation failed: {s_data}")
        time.sleep(0.5)

    r_resp = client.get(f"/api/v1/simulate/{run_id}/result")
    assert r_resp.status_code == 200
    res = r_resp.json()
    assert "animation" in res
    assert "temperature_curves" in res
    assert "analysis_result" in res
    assert res["solver_name"] == "MATLAB_FDM"
    assert len(res["animation"]["surface_temperature"]) == 5
    assert "processing_maps" in res["analysis_result"]


@pytest.mark.matlab
def test_simulation_custom_defect_authoritative():
    payload = {
        "backend": "matlab_fdm",
        "preset": "custom",
        "duration_s": 0.1,
        "timestep_s": 0.05,
        "camera_sampling_rate_hz": 10.0,
        "defects": [
            {
                "diameter_mm": 10.0,
                "depth_mm": 0.5,
                "thickness_mm": 0.4,
                "center_x_mm": 50.0,
                "center_y_mm": 35.0,
                "material": "slag"
            }
        ],
        "spatial_resolution": {"nx": 20, "ny": 14, "nz": 6}
    }
    resp = client.post("/api/v1/simulate", json=payload)
    assert resp.status_code == 200
    run_id = resp.json()["run_id"]

    for _ in range(30):
        s_resp = client.get(f"/api/v1/simulate/{run_id}")
        if s_resp.json()["status"] == "COMPLETED":
            break
        time.sleep(0.5)

    res = client.get(f"/api/v1/simulate/{run_id}/result").json()
    assert res["ground_truth"]["has_defect"] is True
    assert res["ground_truth"]["defects"][0]["diameter_mm"] == 10.0


def test_simulation_invalid_geometry_error():
    payload = {
        "backend": "matlab_fdm",
        "length_mm": -100.0,
        "width_mm": 70.0,
        "thickness_mm": 2.3
    }
    resp = client.post("/api/v1/simulate", json=payload)
    assert resp.status_code == 200
    run_id = resp.json()["run_id"]

    time.sleep(0.8)
    s_resp = client.get(f"/api/v1/simulate/{run_id}")
    assert s_resp.json()["status"] == "FAILED"
    assert "INVALID_GEOMETRY" in s_resp.json()["stage"]


def test_simulation_invalid_depth_error():
    payload = {
        "backend": "matlab_fdm",
        "preset": "custom",
        "thickness_mm": 2.3,
        "defects": [
            {
                "diameter_mm": 8.0,
                "depth_mm": 2.1,
                "thickness_mm": 0.5,  # 2.1 + 0.5 = 2.6 > 2.3
                "center_x_mm": 50.0,
                "center_y_mm": 35.0,
                "material": "slag"
            }
        ]
    }
    resp = client.post("/api/v1/simulate", json=payload)
    assert resp.status_code == 200
    run_id = resp.json()["run_id"]

    time.sleep(0.8)
    s_resp = client.get(f"/api/v1/simulate/{run_id}")
    assert s_resp.json()["status"] == "FAILED"
    assert "INVALID_DEFECT_DEPTH" in s_resp.json()["stage"]

