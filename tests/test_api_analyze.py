"""
Integration tests for FastAPI /api/v1/analyze endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_root_health():
    """Verify health endpoint."""
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_preset_single_thermal_frame():
    """Verify preset single thermal frame analysis."""
    resp = client.post("/api/v1/analyze/preset/single_thermal_frame")
    assert resp.status_code == 200
    data = resp.json()
    assert "analysis_id" in data
    assert data["input_summary"]["input_type"] == "THERMAL_SINGLE_IMAGE"
    assert data["applicability_matrix"]["methods"]["single_frame_spatial"]["is_applicable"] is True
    assert data["applicability_matrix"]["methods"]["pct"]["is_applicable"] is False


def test_preset_healthy_plate():
    """Verify preset healthy plate analysis."""
    resp = client.post("/api/v1/analyze/preset/healthy_plate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["consensus_verdict"]["likely_defect_type"] == "HEALTHY"
    assert data["consensus_verdict"]["is_anomaly_detected"] is False


def test_preset_synthetic_lfmt_slag():
    """Verify preset LFMT slag analysis."""
    resp = client.post("/api/v1/analyze/preset/synthetic_lfmt_slag")
    assert resp.status_code == 200
    data = resp.json()
    assert data["applicability_matrix"]["methods"]["lfmt_matched_filter"]["is_applicable"] is True
    assert data["applicability_matrix"]["methods"]["pct"]["is_applicable"] is True
    assert data["consensus_verdict"]["is_anomaly_detected"] is True
