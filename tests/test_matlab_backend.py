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
    cfg.geometry.inclusion.diameter_mm = 8.0
    cfg.geometry.inclusion.depth_mm = 0.4

    backend = MATLABFDMBackend(mode="engine")
    res = backend.run(cfg)

    assert res.surface_temperature.shape == (5, 28, 40)
    assert np.all(np.isfinite(res.surface_temperature))
    assert res.ground_truth.has_defect is True
    assert res.ground_truth.diameter_mm == 8.0
