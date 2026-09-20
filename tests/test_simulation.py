"""Unit tests for simulation backends and thermal physics (FDM and genuine FEM)."""

import pytest
import numpy as np
from lfmt.config import load_config
from lfmt.simulation import get_simulation_backend, FiniteDifferenceBackend, FEMBackend


def test_backend_factory():
    backend_fdm = get_simulation_backend("finite_difference")
    assert backend_fdm.backend_type == "finite_difference"
    assert not backend_fdm.is_fem

    backend_fem = get_simulation_backend("fem")
    assert backend_fem.backend_type == "fem"
    assert backend_fem.is_fem
    assert backend_fem.is_engine_available


def test_fdm_simulation_run_quick():
    config = load_config("configs/quick.yaml")
    config.simulation.spatial_resolution = {"nx": 20, "ny": 14, "nz": 10}
    config.simulation.total_time_s = 2.0
    config.simulation.timestep_s = 0.2

    backend = FiniteDifferenceBackend()
    res = backend.run(config)

    assert res.surface_temperature.ndim == 3
    n_frames, ny, nx = res.surface_temperature.shape
    assert ny == 14
    assert nx == 20
    assert len(res.time_vector) == n_frames

    T_amb = config.excitation.ambient_temp_k
    assert np.all(res.surface_temperature >= T_amb - 1e-3)
    assert np.max(res.surface_temperature) > T_amb + 0.1
    assert res.ground_truth.has_defect


def test_fem_simulation_run_quick():
    """Verify genuine 3D Finite Element Method execution."""
    config = load_config("configs/quick.yaml")
    config.simulation.spatial_resolution = {"nx": 14, "ny": 10, "nz": 6}
    config.simulation.total_time_s = 2.0
    config.simulation.timestep_s = 0.2

    fem = FEMBackend()
    assert fem.is_engine_available
    res = fem.run(config)

    assert res.backend_name == "fem"
    assert res.surface_temperature.ndim == 3
    assert len(res.time_vector) == res.surface_temperature.shape[0]

    T_amb = config.excitation.ambient_temp_k
    assert np.all(res.surface_temperature >= T_amb - 1e-3)
    assert np.max(res.surface_temperature) > T_amb + 0.1
    assert res.ground_truth.has_defect
    assert "ElementHex1" in res.metadata["engine"]
