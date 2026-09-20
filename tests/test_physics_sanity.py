"""
Fundamental Thermal Physics Sanity Tests for LFMT Simulation.

Validates:
- TEST A: Thermal Equilibrium with zero flux (T == T_ambient)
- TEST B: Positive surface temperature rise under non-negative heating
- TEST C: Strict monotonicity with applied heat flux amplitude (0.5 q0 < 1.0 q0 < 2.0 q0)
- TEST D: Defect depth contrast monotonicity (shallower defects produce higher surface contrast)
- TEST E: Material equality defect invisibility (k_defect == k_steel => contrast == 0)
- TEST F: Spatial symmetry around center for symmetric geometry & excitation
"""

import pytest
import numpy as np
from lfmt.config import load_config
from lfmt.simulation.finite_difference import FiniteDifferenceBackend
from lfmt.contrast import RawThermalContrast


def test_physics_sanity_a_equilibrium():
    """TEST A: Plate with q(t) = 0 and T_init = T_amb must stay at T_amb."""
    cfg = load_config("configs/quick.yaml")
    cfg.simulation.spatial_resolution = {"nx": 20, "ny": 14, "nz": 8}
    cfg.simulation.total_time_s = 1.0
    cfg.simulation.timestep_s = 0.2
    cfg.excitation.q0_w_m2 = 0.0  # Zero heat flux

    backend = FiniteDifferenceBackend()
    res = backend.run(cfg)

    T_amb = cfg.excitation.ambient_temp_k
    max_dev = float(np.max(np.abs(res.surface_temperature - T_amb)))
    assert max_dev < 1e-6, f"Equilibrium violated: max deviation = {max_dev} K"


def test_physics_sanity_b_positive_heating():
    """TEST B: With q(t) > 0, surface temperature must increase above initial."""
    cfg = load_config("configs/quick.yaml")
    cfg.simulation.spatial_resolution = {"nx": 20, "ny": 14, "nz": 8}
    cfg.simulation.total_time_s = 2.0
    cfg.simulation.timestep_s = 0.2
    cfg.excitation.q0_w_m2 = 5000.0

    backend = FiniteDifferenceBackend()
    res = backend.run(cfg)

    T_amb = cfg.excitation.ambient_temp_k
    assert np.max(res.surface_temperature) > T_amb + 0.1
    # Check that minimum temperature never drops below ambient when ambient convection applies
    assert np.min(res.surface_temperature) >= T_amb - 1e-4


def test_physics_sanity_c_flux_monotonicity():
    """TEST C: Higher flux amplitude must produce strictly greater thermal rise."""
    backend = FiniteDifferenceBackend()
    rises = []

    for scale in [0.5, 1.0, 2.0]:
        cfg = load_config("configs/quick.yaml")
        cfg.simulation.spatial_resolution = {"nx": 20, "ny": 14, "nz": 8}
        cfg.simulation.total_time_s = 2.0
        cfg.simulation.timestep_s = 0.2
        cfg.excitation.q0_w_m2 = 5000.0 * scale

        res = backend.run(cfg)
        T_amb = cfg.excitation.ambient_temp_k
        max_rise = float(np.max(res.surface_temperature) - T_amb)
        rises.append(max_rise)

    assert rises[0] < rises[1] < rises[2], f"Flux monotonicity failed: {rises}"


def test_physics_sanity_d_depth_trend():
    """TEST D: Shallower defects produce higher surface peak thermal contrast."""
    backend = FiniteDifferenceBackend()
    contrast_eval = RawThermalContrast()
    peak_contrasts = []

    for depth in [0.3, 0.6, 0.9]:
        cfg = load_config("configs/quick.yaml")
        cfg.simulation.spatial_resolution = {"nx": 30, "ny": 20, "nz": 16}
        cfg.simulation.total_time_s = 3.0
        cfg.simulation.timestep_s = 0.1
        cfg.geometry.inclusion.depth_mm = depth
        cfg.geometry.inclusion.diameter_mm = 8.0

        res = backend.run(cfg)
        
        # Center pixel vs Corner sound pixel
        ny, nx = res.surface_temperature.shape[1], res.surface_temperature.shape[2]
        center_t = res.surface_temperature[:, ny // 2, nx // 2]
        sound_t = res.surface_temperature[:, 2, 2]
        delta_t = np.max(np.abs(center_t - sound_t))
        peak_contrasts.append(delta_t)

    assert peak_contrasts[0] > peak_contrasts[1] > peak_contrasts[2], (
        f"Depth contrast trend violated: {peak_contrasts}"
    )


def test_physics_sanity_e_material_equality():
    """TEST E: If inclusion material is set equal to steel, contrast is zero."""
    cfg = load_config("configs/quick.yaml")
    cfg.simulation.spatial_resolution = {"nx": 20, "ny": 14, "nz": 8}
    cfg.simulation.total_time_s = 2.0
    cfg.simulation.timestep_s = 0.2
    cfg.geometry.inclusion.material = "mild_steel"  # Inclusion is mild steel matrix

    backend = FiniteDifferenceBackend()
    res = backend.run(cfg)

    ny, nx = res.surface_temperature.shape[1], res.surface_temperature.shape[2]
    center_t = res.surface_temperature[:, ny // 2, nx // 2]
    sound_t = res.surface_temperature[:, 2, 2]
    max_contrast = float(np.max(np.abs(center_t - sound_t)))

    assert max_contrast < 1e-4, f"Material equality failed: contrast = {max_contrast} K"


def test_physics_sanity_f_spatial_symmetry():
    """TEST F: Symmetric centered defect and uniform flux must produce symmetric thermal field."""
    cfg = load_config("configs/quick.yaml")
    cfg.simulation.spatial_resolution = {"nx": 28, "ny": 28, "nz": 8}
    cfg.geometry.plate.length_mm = 70.0
    cfg.geometry.plate.width_mm = 70.0
    cfg.geometry.inclusion.center_x_mm = 35.0
    cfg.geometry.inclusion.center_y_mm = 35.0
    cfg.simulation.total_time_s = 2.0
    cfg.simulation.timestep_s = 0.2

    backend = FiniteDifferenceBackend()
    res = backend.run(cfg)

    # Check symmetry across X and Y axes on the surface at final frame
    final_surf = res.surface_temperature[-1]
    # Flip left-right
    sym_err_x = np.max(np.abs(final_surf - np.fliplr(final_surf)))
    # Flip up-down
    sym_err_y = np.max(np.abs(final_surf - np.flipud(final_surf)))

    assert sym_err_x < 1e-5, f"X-symmetry error: {sym_err_x}"
    assert sym_err_y < 1e-5, f"Y-symmetry error: {sym_err_y}"
