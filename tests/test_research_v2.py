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


def test_experimental_data_loader():
    """Verify ExperimentalDataLoader format ingestion and validation."""
    os.makedirs("results/research_v2/tmp_test", exist_ok=True)
    try:
        test_cube = np.ones((20, 32, 32), dtype=np.float64) * 295.0
        npy_path = "results/research_v2/tmp_test/test_seq.npy"
        np.save(npy_path, test_cube)

        seq = ExperimentalDataLoader.load_numpy(npy_path, frame_rate_hz=25.0, fov_mm=(100.0, 70.0))
        assert seq.surface_temperature.shape == (20, 32, 32)
        assert len(seq.time_vector) == 20
        assert np.isclose(seq.frame_rate_hz, 25.0)

        val = ExperimentalDataLoader.validate_sequence(seq)
        assert val["is_valid"] is True
        assert val["total_duration_s"] > 0.7
    finally:
        if os.path.exists("results/research_v2/tmp_test"):
            shutil.rmtree("results/research_v2/tmp_test", ignore_errors=True)


