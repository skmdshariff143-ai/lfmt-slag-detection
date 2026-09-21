"""
Integration and unit tests for /api/v1/examples REST endpoints.
"""

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_get_examples_list():
    resp = client.get("/api/v1/examples")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 6
    
    ids = [item["id"] for item in data]
    assert "healthy_lfmt" in ids
    assert "slag_shallow" in ids
    assert "measured_polyu_preview" in ids


def test_get_example_details_success():
    resp = client.get("/api/v1/examples/slag_shallow")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "slag_shallow"
    assert data["integrity"]["status"] == "VERIFIED"
    assert data["category"] in ["A", "Category A: Numerical 3D FEM"]
    assert "metadata" in data


def test_get_example_details_404():
    resp = client.get("/api/v1/examples/nonexistent_example_id")
    assert resp.status_code == 404
    err = resp.json()
    assert "detail" in err


def test_analyze_healthy_example():
    resp = client.post("/api/v1/examples/healthy_lfmt/analyze?apply_baseline=true&smooth_sigma_px=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert "analysis_id" in data
    
    consensus = data["consensus_verdict"]
    assert consensus["is_anomaly_detected"] is False
    assert consensus["likely_defect_type"] == "HEALTHY"


def test_analyze_slag_shallow_example():
    resp = client.post("/api/v1/examples/slag_shallow/analyze?apply_baseline=true&smooth_sigma_px=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert "analysis_id" in data
    
    consensus = data["consensus_verdict"]
    assert consensus["is_anomaly_detected"] is True
    # In V3, unvalidated classifier produces generic subsurface thermal anomaly
    assert consensus["likely_defect_type"] == "GENERIC_SUBSURFACE_THERMAL_ANOMALY"
    assert len(data["defects"]) >= 1


def test_analyze_single_frame_example():
    resp = client.post("/api/v1/examples/single_thermal_frame/analyze")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["input_summary"]["input_type"] == "THERMAL_SINGLE_IMAGE"
    assert data["applicability_matrix"]["methods"]["single_frame_spatial"]["is_applicable"] is True
    assert data["applicability_matrix"]["methods"]["pct"]["is_applicable"] is False


def test_analyze_measured_polyu():
    resp = client.post("/api/v1/examples/measured_polyu_preview/analyze")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["SUCCESS", "EXTERNAL_DATA_NOT_INSTALLED"]


def test_lfmt_anomaly_does_not_imply_slag_without_validated_model():
    """
    Scientific Non-Overclaiming Gate:
    Verify that an LFMT anomaly (even with high Matched Filter SNR) strictly classifies
    as GENERIC_SUBSURFACE_THERMAL_ANOMALY, never automatically as SLAG_INCLUSION,
    when no validated neural/tabular classifier checkpoint is loaded.
    """
    for example_id in ["slag_shallow", "slag_deep", "multi_slag"]:
        resp = client.post(f"/api/v1/examples/{example_id}/analyze")
        assert resp.status_code == 200
        data = resp.json()
        assert data["consensus_verdict"]["is_anomaly_detected"] is True
        assert data["consensus_verdict"]["likely_defect_type"] == "GENERIC_SUBSURFACE_THERMAL_ANOMALY"
        assert data["consensus_verdict"]["likely_defect_type"] != "SLAG_INCLUSION"
