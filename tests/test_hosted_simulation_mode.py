"""
Test suite verifying the Hosted Simulation and Precomputed Demo contract.
Ensures precomputed artifact schema, frame counts, camera timing, and runtime decoupling.
"""

import json
from pathlib import Path
import pytest


def test_precomputed_matlab_artifact_schema():
    """Verify precomputed MATLAB demo artifact has all required fields and correct physics."""
    demo_path = Path(__file__).resolve().parent.parent / "web" / "public" / "demo" / "matlab_shallow_slag.json"
    assert demo_path.exists(), f"Precomputed artifact missing at {demo_path}"

    data = json.loads(demo_path.read_text(encoding="utf-8"))

    # Required core fields
    required_keys = [
        "run_id",
        "backend",
        "solver_name",
        "is_precomputed",
        "execution_time_s",
        "solver_dt_s",
        "camera_frame_rate_hz",
        "time_vector",
        "animation",
        "temperature_curves",
        "analysis_result",
        "ground_truth",
    ]
    for k in required_keys:
        assert k in data, f"Key '{k}' missing in precomputed demo artifact"

    # Backend & Solver naming
    assert data["backend"] == "matlab_fdm"
    assert data["solver_name"] == "MATLAB_FDM"
    assert data["is_precomputed"] is True

    # Temporal & Camera parameters
    assert data["camera_frame_rate_hz"] == 10.0
    assert data["solver_dt_s"] == 0.04
    time_vec = data["time_vector"]
    assert len(time_vec) == 101, f"Expected 101 temporal frames, got {len(time_vec)}"
    assert pytest.approx(time_vec[-1] - time_vec[0], 0.01) == 10.0  # 10 s duration
    assert pytest.approx(time_vec[1] - time_vec[0], 0.001) == 0.1  # 10 Hz camera interval (0.1 s)

    # Animation matrix dimensions
    surf_temp = data["animation"]["surface_temperature"]
    delta_t = data["animation"]["delta_t"]
    assert len(surf_temp) == 101
    assert len(delta_t) == 101
    assert len(surf_temp[0]) == 64  # ny
    assert len(surf_temp[0][0]) == 64  # nx

    # Analysis result and processing maps
    ar = data["analysis_result"]
    assert "consensus_verdict" in ar
    assert ar["consensus_verdict"]["is_anomaly_detected"] is True
    assert "processing_maps" in ar
    for m in ["raw", "pct", "spct", "rpt"]:
        assert m in ar["processing_maps"], f"Map '{m}' missing in precomputed processing maps"

    # Ground truth isolation
    gt = data["ground_truth"]
    assert gt["has_defect"] is True
    assert gt["defects"][0]["diameter_mm"] == 8.0
    assert gt["defects"][0]["depth_mm"] == 0.4
