"""
Tests for loading and deserializing MATLAB .mat simulation artifacts.
"""

import tempfile
from pathlib import Path
import numpy as np
import scipy.io
import pytest

from lfmt.config import load_config
from lfmt.simulation.matlab_backend import MATLABFDMBackend
from lfmt.matlab.environment import detect_matlab_environment


@pytest.mark.matlab
def test_export_and_load_mat():
    env = detect_matlab_environment()
    if not env.get("matlab_available", False):
        pytest.skip("MATLAB is not available.")

    cfg = load_config("configs/research_v3_high_fidelity.yaml")
    cfg.simulation.spatial_resolution["nx"] = 20
    cfg.simulation.spatial_resolution["ny"] = 14
    cfg.simulation.spatial_resolution["nz"] = 6
    cfg.simulation.total_time_s = 0.2
    cfg.simulation.timestep_s = 0.1

    backend = MATLABFDMBackend(mode="batch")
    res = backend.run(cfg)

    with tempfile.TemporaryDirectory() as tmpdir:
        out_mat = Path(tmpdir) / "sim_result.mat"
        scipy.io.savemat(str(out_mat), {
            "surface_temperature": res.surface_temperature,
            "time_vector": res.time_vector,
            "camera_x_mm": res.x_grid_mm,
            "camera_y_mm": res.y_grid_mm
        })

        loaded = scipy.io.loadmat(str(out_mat))
        assert "surface_temperature" in loaded
        assert loaded["surface_temperature"].shape == res.surface_temperature.shape
        assert np.allclose(loaded["surface_temperature"], res.surface_temperature)
