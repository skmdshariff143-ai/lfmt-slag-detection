"""
Verification tests for the Python FEM vs. MATLAB FDM physics contract.
"""

import numpy as np
import pytest
from lfmt.config import load_config
from lfmt.simulation.matlab_backend import MATLABFDMBackend
from lfmt.matlab.environment import detect_matlab_environment


@pytest.mark.matlab
def test_matlab_fdm_execution_and_contract():
    env = detect_matlab_environment()
    if not env.get("matlab_available", False):
        pytest.skip("MATLAB is not installed in the environment.")

    cfg = load_config("configs/research_v3_high_fidelity.yaml")
    # Fast test configuration (coarse grid, short duration for unit test)
    cfg.simulation.spatial_resolution["nx"] = 20
    cfg.simulation.spatial_resolution["ny"] = 14
    cfg.simulation.spatial_resolution["nz"] = 6
    cfg.simulation.total_time_s = 0.5
    cfg.simulation.timestep_s = 0.1
    cfg.geometry.inclusion.diameter_mm = 0.0

    backend = MATLABFDMBackend(mode="batch")
    res = backend.run(cfg)

    # 1. Dimension and type invariant
    assert res.surface_temperature.ndim == 3
    assert res.surface_temperature.shape == (6, cfg.camera.resolution_y, cfg.camera.resolution_x)
    assert np.all(np.isfinite(res.surface_temperature))

    # 2. Frame 0 ambient invariant
    Tamb = cfg.excitation.ambient_temp_k
    assert np.max(np.abs(res.surface_temperature[0] - Tamb)) == 0.0

    # 3. Solver identification invariant
    assert res.backend_name == "matlab_fdm"
    assert res.metadata["solver_name"] == "MATLAB_FDM"
    assert "Finite Difference" in res.metadata["discretization_method"]
