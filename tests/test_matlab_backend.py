"""
Integration and unit tests for MATLABFDMBackend.
"""

import pytest
import numpy as np
from lfmt.config import load_config
from lfmt.simulation.matlab_backend import MATLABFDMBackend
from lfmt.matlab.environment import detect_matlab_environment


@pytest.mark.matlab
def test_matlab_fdm_engine_mode():
    env = detect_matlab_environment()
    if not env.get("matlab_engine_importable", False):
        pytest.skip("MATLAB Engine is not importable.")

    cfg = load_config("configs/research_v3_high_fidelity.yaml")
    cfg.simulation.spatial_resolution["nx"] = 20
    cfg.simulation.spatial_resolution["ny"] = 14
    cfg.simulation.spatial_resolution["nz"] = 6
    cfg.simulation.total_time_s = 0.4
    cfg.simulation.timestep_s = 0.1
    cfg.camera.sampling_rate_hz = 10.0
    cfg.camera.resolution_x = 40
    cfg.camera.resolution_y = 28
    cfg.geometry.inclusion.diameter_mm = 8.0
    cfg.geometry.inclusion.depth_mm = 0.4

    backend = MATLABFDMBackend(mode="engine")
    res = backend.run(cfg)

    assert res.surface_temperature.shape == (5, 28, 40)
    assert np.all(np.isfinite(res.surface_temperature))
    assert res.ground_truth.has_defect is True
    assert res.ground_truth.diameter_mm == 8.0


@pytest.mark.matlab
def test_matlab_multi_defect_simulation():
    """Verify MATLAB backend serializes and simulates multiple defect regions."""
    env = detect_matlab_environment()
    if not env.get("matlab_engine_importable", False):
        pytest.skip("MATLAB Engine is not importable.")

    cfg = load_config("configs/research_v3_high_fidelity.yaml")
    cfg.simulation.spatial_resolution["nx"] = 40
    cfg.simulation.spatial_resolution["ny"] = 28
    cfg.simulation.spatial_resolution["nz"] = 12
    cfg.simulation.total_time_s = 0.2
    cfg.simulation.timestep_s = 0.04
    cfg.camera.sampling_rate_hz = 10.0
    cfg.camera.resolution_x = 40
    cfg.camera.resolution_y = 28

    cfg.geometry.inclusion.inclusions_list = [
        {"diameter_mm": 6.0, "depth_mm": 0.4, "thickness_mm": 0.4, "center_x_mm": 42.5, "center_y_mm": 35.0, "material": "slag"},
        {"diameter_mm": 4.8, "depth_mm": 0.4, "thickness_mm": 0.4, "center_x_mm": 57.5, "center_y_mm": 35.0, "material": "slag"}
    ]

    backend = MATLABFDMBackend(mode="engine")
    res = backend.run(cfg)

    assert res.metadata["defects_simulated"] == 2
    assert res.surface_temperature.shape == (3, 28, 40)
    assert np.all(np.isfinite(res.surface_temperature))
    assert res.ground_truth.has_defect is True


@pytest.mark.matlab
def test_matlab_custom_parameters_authoritative():
    """Verify custom parameter overrides (e.g. D=10mm) are authoritative."""
    env = detect_matlab_environment()
    if not env.get("matlab_engine_importable", False):
        pytest.skip("MATLAB Engine is not importable.")

    cfg = load_config("configs/research_v3_high_fidelity.yaml")
    cfg.simulation.spatial_resolution["nx"] = 20
    cfg.simulation.spatial_resolution["ny"] = 14
    cfg.simulation.spatial_resolution["nz"] = 6
    cfg.simulation.total_time_s = 0.1
    cfg.simulation.timestep_s = 0.05
    cfg.camera.sampling_rate_hz = 10.0
    cfg.camera.resolution_x = 40
    cfg.camera.resolution_y = 28
    cfg.geometry.inclusion.diameter_mm = 10.0
    cfg.geometry.inclusion.depth_mm = 0.5
    cfg.geometry.inclusion.inclusions_list = []

    backend = MATLABFDMBackend(mode="engine")
    res = backend.run(cfg)

    assert res.ground_truth.diameter_mm == 10.0
    assert res.ground_truth.depth_mm == 0.5


@pytest.mark.matlab
def test_matlab_decoupled_camera_fps_and_solver_dt():
    """Verify solver dt (0.04s) is decoupled from camera FPS (10Hz)."""
    env = detect_matlab_environment()
    if not env.get("matlab_engine_importable", False):
        pytest.skip("MATLAB Engine is not importable.")

    cfg = load_config("configs/research_v3_high_fidelity.yaml")
    cfg.simulation.spatial_resolution["nx"] = 20
    cfg.simulation.spatial_resolution["ny"] = 14
    cfg.simulation.spatial_resolution["nz"] = 6
    cfg.simulation.total_time_s = 1.0
    cfg.simulation.timestep_s = 0.04  # 26 solver steps
    cfg.camera.sampling_rate_hz = 10.0 # 11 camera frames
    cfg.camera.resolution_x = 40
    cfg.camera.resolution_y = 28

    backend = MATLABFDMBackend(mode="engine")
    res = backend.run(cfg)

    # Number of camera frames must be exactly 11 (0.0, 0.1, 0.2, ..., 1.0)
    assert res.surface_temperature.shape[0] == 11
    assert len(res.time_vector) == 11
    assert res.metadata["solver_dt_s"] == 0.04
    assert res.metadata["camera_frame_rate_hz"] == 10.0

