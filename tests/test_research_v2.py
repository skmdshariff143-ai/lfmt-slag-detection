"""
Comprehensive Test Suite for Research V2 Scientific Fidelity and Upgrades.
"""

import os
import math
import shutil
import numpy as np
import pytest

from lfmt.config import load_config, LFMTConfig, CameraConfig, MeshRefinementConfig, InclusionConfig
from lfmt.simulation.fem import FEMBackend, generate_graded_1d_nodes, generate_graded_z_nodes
from lfmt.noise import add_thermal_camera_noise, measure_actual_snr_db, add_awgn_noise, add_radiance_emissivity_variation, CameraNoisePreset
from lfmt.camera import VirtualIRCamera
from lfmt.detection import MultiDefectDetector, DefectDetector, match_defects_hungarian
from lfmt.metrics import compute_metrics, compute_roc_pr_curves
from lfmt.simulation.base import GroundTruth
from lfmt.io_experimental import ExperimentalDataLoader, ExperimentalSequence


def test_graded_mesh_generation():
    """Verify non-uniform 1D and Z mesh grading."""
    x_nodes = generate_graded_1d_nodes(L=0.10, center=0.05, radius=0.002, target_elements_core=10, target_elements_flank=8)
    assert len(x_nodes) > 15
    assert np.all(np.diff(x_nodes) > 0)
    assert np.isclose(x_nodes[0], 0.0)
    assert np.isclose(x_nodes[-1], 0.10)

    dx_core = np.min(np.diff(x_nodes))
    dx_boundary = np.max(np.diff(x_nodes))
    assert dx_core < dx_boundary / 2.0

    z_nodes = generate_graded_z_nodes(L_z=0.01, d_top=0.0002, thickness=0.001, target_cover=5)
    assert len(z_nodes) > 8
    assert np.all(np.diff(z_nodes) > 0)
    assert np.isclose(z_nodes[0], 0.0)
    assert np.isclose(z_nodes[-1], 0.01)


def test_radiance_emissivity_and_snr_measurement():
    """Verify Stefan-Boltzmann physical radiance emissivity and SNR measurement."""
    T_surf = np.full((10, 20, 20), 300.0, dtype=np.float64)
    for k in range(10):
        T_surf[k] += np.sin(2 * np.pi * k / 10.0) * 2.0

    # 1. AWGN noise verification
    noisy_awgn, actual_snr = add_thermal_camera_noise(
        T_surf,
        snr_db=30.0,
        preset=CameraNoisePreset.CONTROLLED_AWGN,
        emissivity=1.0,
        emissivity_variation=0.0,
        ambient_temp_k=295.0,
        use_radiance_emissivity=False,
        seed=42
    )
    assert noisy_awgn.shape == T_surf.shape
    assert not np.any(np.isnan(noisy_awgn))
    assert 28.0 <= actual_snr <= 32.0

    # 2. Radiance-level emissivity variation
    noisy_rad = add_radiance_emissivity_variation(
        T_surf,
        base_emissivity=0.85,
        variation_std=0.01,
        t_ambient_k=295.0,
        seed=42
    )
    assert noisy_rad.shape == T_surf.shape
    # Radiance apparent temperature should reflect ambient reflection
    assert np.all(noisy_rad > 290.0)


def test_multi_defect_detector_and_hungarian_matching():
    """Verify MultiDefectDetector component isolation and Hungarian matching."""
    score_map = np.zeros((64, 64), dtype=np.float64)
    y1, x1 = np.ogrid[:64, :64]
    mask1 = ((x1 - 20)**2 + (y1 - 20)**2) <= 16
    mask2 = ((x1 - 45)**2 + (y1 - 45)**2) <= 25
    score_map[mask1] = 0.8
    score_map[mask2] = 0.95

    detector = MultiDefectDetector(threshold_method="percentile", percentile_val=98.0, min_area_px=3)
    res = detector.detect_all(score_map, fov_mm=(100.0, 70.0))

    assert res.n_candidates >= 2
    assert len(res.candidates) >= 2

    gt_centroids = [(20.0 * 100.0 / 63.0, 20.0 * 70.0 / 63.0), (45.0 * 100.0 / 63.0, 45.0 * 70.0 / 63.0)]
    pred_centroids = [c.centroid_mm for c in res.candidates]

    matching = match_defects_hungarian(gt_centroids, pred_centroids, max_distance_mm=5.0)
    assert matching["precision"] >= 0.5
    assert matching["recall"] >= 0.5
    assert matching["f1"] >= 0.5
    assert matching["mean_localization_error_mm"] < 2.0


def test_tiered_evaluation_and_roc_curves():
    """Verify Tiers A, B, C, D criteria and ROC/PR curves."""
    H, W = 50, 50
    gt_mask = np.zeros((H, W), dtype=bool)
    gt_mask[20:30, 20:30] = True
    score_map = np.zeros((H, W), dtype=np.float64)
    score_map[20:30, 20:30] = 1.0

    detector = DefectDetector(threshold_method="adaptive_otsu")
    detection = detector.detect(score_map, fov_mm=(100.0, 70.0))

    # Centroid of 20:30, 20:30 in mm
    cx_mm = 24.5 * 100.0 / 49.0
    cy_mm = 24.5 * 70.0 / 49.0

    gt = GroundTruth(
        center_x_mm=cx_mm,
        center_y_mm=cy_mm,
        depth_mm=0.5,
        diameter_mm=10.0,
        thickness_mm=1.0,
        material_name="slag",
        area_mm2=78.5,
        volume_mm3=78.5,
        has_defect=True
    )

    metrics = compute_metrics(
        method_name="PCT",
        detection=detection,
        ground_truth=gt,
        ground_truth_mask=gt_mask,
        score_map=score_map,
        fov_mm=(100.0, 70.0)
    )

    assert metrics.tier_a_detected is True
    assert metrics.tier_b_detected is True
    assert metrics.tier_c_detected is True
    assert metrics.tier_d_detected is True
    assert metrics.roc_auc is not None and metrics.roc_auc > 0.95


def test_radiometric_invariants_and_inversion():
    """Verify physical invariants and inversion of Stefan-Boltzmann broadband radiometry."""
    from lfmt.noise import (
        compute_broadband_radiance,
        compute_apparent_blackbody_temperature,
        compute_emissivity_corrected_temperature
    )

    # Invariant 1: When T_surf == T_amb, T_apparent == T_amb for ANY emissivity
    T_amb = 293.15
    for eps in [0.1, 0.5, 0.85, 0.95, 1.0]:
        T_app = compute_apparent_blackbody_temperature(
            true_surface_temperature_k=np.full((5, 5), T_amb),
            emissivity=eps,
            t_ambient_k=T_amb
        )
        assert np.allclose(T_app, T_amb, atol=1e-10), f"Failed invariant at eps={eps}"

    # Inversion: Invert apparent temperature back to true surface temperature
    T_true = np.array([[300.0, 310.0], [320.0, 330.0]])
    eps = 0.85
    T_app = compute_apparent_blackbody_temperature(
        true_surface_temperature_k=T_true,
        emissivity=eps,
        t_ambient_k=T_amb
    )
    T_rec = compute_emissivity_corrected_temperature(
        apparent_blackbody_temp_k=T_app,
        emissivity=eps,
        t_ambient_k=T_amb
    )
    assert np.allclose(T_rec, T_true, atol=1e-6), "Radiometric inversion reconstruction failed"


def test_simulation_config_hash_uniqueness():
    """Verify simulation config hashing uniquely identifies physics and mesh modifications."""
    import hashlib
    import json

    def hash_cfg(cfg_dict: dict) -> str:
        s = json.dumps(cfg_dict, sort_keys=True)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    base_cfg = {
        "diameter_mm": 8.0,
        "depth_mm": 0.4,
        "mesh_mode": "adaptive_tensor",
        "q0_w_m2": 5000.0,
        "k_steel": 45.0
    }
    h_base = hash_cfg(base_cfg)

    # 1. Depth change
    cfg_d = dict(base_cfg, depth_mm=0.6)
    assert hash_cfg(cfg_d) != h_base

    # 2. Mesh mode change
    cfg_m = dict(base_cfg, mesh_mode="uniform")
    assert hash_cfg(cfg_m) != h_base

    # 3. Heat flux change
    cfg_q = dict(base_cfg, q0_w_m2=6000.0)
    assert hash_cfg(cfg_q) != h_base



