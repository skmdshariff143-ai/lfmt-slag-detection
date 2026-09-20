"""
Audit Integrity Unit Tests.

Tests the scientific and numerical integrity of metric evaluations,
healthy control false-positive logic, localization error NaN handling,
and PDE parameter sensitivity hash invalidation.
"""

import math
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from lfmt.config import LFMTConfig, load_config
from lfmt.detection import DetectionResult, DefectDetector
from lfmt.simulation.base import GroundTruth
from lfmt.metrics import compute_metrics, EvaluationMetrics
from lfmt.experiments import compute_config_hash


def test_metric_localization_nan_on_no_detection():
    """Verify that when no candidate or no detection is made, localization error is NaN, not 0.0 mm."""
    # Dummy empty detection
    det_empty = DetectionResult(
        predicted_mask=np.zeros((32, 32), dtype=bool),
        is_detected=False,
        centroid_px=(math.nan, math.nan),
        centroid_mm=(math.nan, math.nan),
        equivalent_diameter_mm=0.0,
        area_px=0,
        area_mm2=0.0,
        threshold_value=0.0,
        threshold_method="adaptive_otsu",
        bounding_box_px=None,
        confidence_score=0.0,
        runtime_seconds=0.01,
        metadata={}
    )
    
    gt = GroundTruth(
        center_x_mm=50.0,
        center_y_mm=35.0,
        depth_mm=0.4,
        diameter_mm=8.0,
        thickness_mm=0.5,
        material_name="welding_slag_silicate",
        area_mm2=math.pi * 16.0,
        volume_mm3=math.pi * 16.0 * 0.5,
        has_defect=True
    )
    gt_mask = np.zeros((32, 32), dtype=bool)
    gt_mask[14:18, 14:18] = True
    processed_map = np.zeros((32, 32))
    
    met = compute_metrics("TestPCT", det_empty, gt, gt_mask, processed_map, 0.01, (100.0, 70.0))
    
    assert met.is_detected is False
    assert math.isnan(met.localization_error_detected_mm)
    assert math.isnan(met.localization_error_all_mm)
    assert math.isnan(met.localization_error_mm)


def test_healthy_specimen_independent_false_positive():
    """Verify healthy control false positive behavior."""
    gt_healthy = GroundTruth(
        center_x_mm=math.nan,
        center_y_mm=math.nan,
        depth_mm=0.0,
        diameter_mm=0.0,
        thickness_mm=0.0,
        material_name="none",
        area_mm2=0.0,
        volume_mm3=0.0,
        has_defect=False
    )
    gt_mask_healthy = np.zeros((32, 32), dtype=bool)
    processed_map = np.zeros((32, 32))
    
    # Case A: No candidate detected on healthy
    det_healthy_clean = DetectionResult(
        predicted_mask=np.zeros((32, 32), dtype=bool),
        is_detected=False,
        centroid_px=(math.nan, math.nan),
        centroid_mm=(math.nan, math.nan),
        equivalent_diameter_mm=0.0,
        area_px=0,
        area_mm2=0.0,
        threshold_value=0.0,
        threshold_method="adaptive_otsu",
        bounding_box_px=None,
        confidence_score=0.0,
        runtime_seconds=0.01,
        metadata={}
    )
    met_a = compute_metrics("TestPCT", det_healthy_clean, gt_healthy, gt_mask_healthy, processed_map, 0.01, (100.0, 70.0))
    assert met_a.candidate_detected is False
    assert met_a.is_detected is False
    assert met_a.is_false_positive is False
    assert math.isnan(met_a.localization_error_detected_mm)

    # Case B: Spurious candidate detected on healthy
    mask_spur = np.zeros((32, 32), dtype=bool)
    mask_spur[5:10, 5:10] = True
    det_healthy_spurious = DetectionResult(
        predicted_mask=mask_spur,
        is_detected=True,
        centroid_px=(7.5, 7.5),
        centroid_mm=(23.4, 16.4),
        equivalent_diameter_mm=5.6,
        area_px=25,
        area_mm2=25.0,
        threshold_value=0.5,
        threshold_method="adaptive_otsu",
        bounding_box_px=(5, 5, 10, 10),
        confidence_score=0.8,
        runtime_seconds=0.01,
        metadata={}
    )
    met_b = compute_metrics("TestPCT", det_healthy_spurious, gt_healthy, gt_mask_healthy, processed_map, 0.01, (100.0, 70.0))
    assert met_b.candidate_detected is True
    assert met_b.is_detected is False
    assert met_b.is_false_positive is True
    assert math.isnan(met_b.localization_error_detected_mm)
    assert math.isnan(met_b.localization_error_all_mm)


def test_sensitivity_pde_parameter_hash_invalidation():
    """Verify that altering physical PDE parameters changes the configuration hash."""
    cfg = load_config("configs/default.yaml")
    hash_base = compute_config_hash(cfg)

    # Alter q0
    cfg_q0 = load_config("configs/default.yaml")
    cfg_q0.excitation.q0_w_m2 = 4500.0
    hash_q0 = compute_config_hash(cfg_q0)
    assert hash_base != hash_q0

    # Alter k_slag
    cfg_k = load_config("configs/default.yaml")
    cfg_k.geometry.inclusion.thermal_conductivity = 1.08
    hash_k = compute_config_hash(cfg_k)
    assert hash_base != hash_k

    # Alter cp_slag
    cfg_cp = load_config("configs/default.yaml")
    cfg_cp.geometry.inclusion.specific_heat = 765.0
    hash_cp = compute_config_hash(cfg_cp)
    assert hash_base != hash_cp


def test_raw_results_integrity():
    """Verify conference benchmark dataset record count, structure, and integrity."""
    raw_path = Path("results/conference/final/raw_results_final.csv")
    if not raw_path.exists():
        raw_path = Path("results/conference/raw_results.csv")
    
    assert raw_path.exists(), "Raw conference results CSV not found!"
    df = pd.read_csv(raw_path)
    
    # 4030 evaluations
    assert len(df) == 4030
    assert len(df[~df["is_healthy"]]) == 3875
    assert len(df[df["is_healthy"]]) == 155
    
    # Zero duplicates
    dup_cols = ["backend", "diameter_mm", "depth_mm", "is_healthy", "noise_condition", "noise_seed", "method"]
    assert df.duplicated(subset=dup_cols).sum() == 0