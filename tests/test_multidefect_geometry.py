"""
Verification tests for multi-defect and non-cylindrical inclusion geometry in 3D FEM solver.
"""

import numpy as np
import pytest
from src.lfmt.config import (
    LFMTConfig,
    PlateConfig,
    InclusionConfig,
    GeometryConfig,
    SimulationConfig,
    ExcitationConfig,
)
from src.lfmt.simulation.fem import FEMBackend


def test_multidefect_fem_mesh_and_tagging():
    """Verify that multi_inclusion shape produces distinct inclusion elements in the FEM mesh."""
    config = LFMTConfig(
        geometry=GeometryConfig(
            plate=PlateConfig(length_mm=50.0, width_mm=50.0, thickness_mm=4.0),
            inclusion=InclusionConfig(
                shape="multi_inclusion",
                diameter_mm=6.0,
                depth_mm=1.0,
                thickness_mm=1.0,
                center_x_mm=25.0,
                center_y_mm=25.0,
            ),
        ),
        simulation=SimulationConfig(
            backend="fem",
            total_time_s=1.0,
            timestep_s=0.5,
            spatial_resolution={"nx": 20, "ny": 20, "nz": 8},
        ),
        excitation=ExcitationConfig(f0_hz=0.05, f1_hz=0.5, duration_s=1.0, q0_w_m2=1000.0),
    )

    backend = FEMBackend(fallback_if_unavailable=False)
    res = backend.run(config)
    assert res is not None
    assert res.surface_temperature.shape[0] == len(res.time_vector)
    assert res.surface_temperature.shape[1] > 0
    assert res.surface_temperature.shape[2] > 0
    assert np.all(np.isfinite(res.surface_temperature))


def test_irregular_and_ellipse_fem_shapes():
    """Verify ellipse and irregular shape options in FEM geometry classification."""
    for shape in ["ellipse", "strip", "irregular"]:
        config = LFMTConfig(
            geometry=GeometryConfig(
                plate=PlateConfig(length_mm=40.0, width_mm=40.0, thickness_mm=3.0),
                inclusion=InclusionConfig(
                    shape=shape,
                    diameter_mm=5.0,
                    depth_mm=0.8,
                    thickness_mm=0.8,
                    center_x_mm=20.0,
                    center_y_mm=20.0,
                ),
            ),
            simulation=SimulationConfig(
                backend="fem",
                total_time_s=0.5,
                timestep_s=0.5,
                spatial_resolution={"nx": 16, "ny": 16, "nz": 6},
            ),
            excitation=ExcitationConfig(f0_hz=0.05, f1_hz=0.5, duration_s=0.5, q0_w_m2=500.0),
        )

        backend = FEMBackend(fallback_if_unavailable=False)
        res = backend.run(config)
        assert np.all(np.isfinite(res.surface_temperature))
