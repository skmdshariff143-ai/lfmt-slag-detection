"""Unit tests for defect detection, segmentation, and evaluation metrics."""

import pytest
import numpy as np
import math
from lfmt.detection import DefectDetector, compute_otsu_threshold
from lfmt.metrics import compute_metrics, EvaluationMetrics
from lfmt.simulation.base import GroundTruth


def test_otsu_threshold():
    img = np.full((30, 30), 0.2)
    img[10:20, 10:20] = 0.8
    thresh = compute_otsu_threshold(img)
    assert 0.2 < thresh < 0.8


def test_defect_detector_blind():
    """Phase 15: Verify detector segments score map without using ground truth."""
    H, W = 40, 40
    Y, X = np.ogrid[:H, :W]
    dist_sq = (Y - 20)**2 + (X - 20)**2
    score_map = np.exp(-dist_sq / (2 * 5**2))  # Gaussian peak

    detector = DefectDetector(threshold_method="adaptive_otsu", min_area_px=4)
    res = detector.detect(score_map, fov_mm=(100.0, 70.0))

    assert res.is_detected
    assert res.predicted_mask.shape == (H, W)
    assert abs(res.centroid_px[0] - 20) < 1.0
    assert abs(res.centroid_px[1] - 20) < 1.0


def test_metric_exact_formulas():
    """Phase 16: Verify exact IoU, Dice, Precision, Recall, and Localization Error in mm and px."""
    H, W = 10, 10
    fov_x_mm, fov_y_mm = 18.0, 18.0  # dx = 18/9 = 2.0 mm/px, dy = 18/9 = 2.0 mm/px
    dx = fov_x_mm / 9.0
    dy = fov_y_mm / 9.0

    # Ground truth: 2x2 square at rows 2..3, cols 2..3 (4 pixels)
    gt_mask = np.zeros((H, W), dtype=bool)
    gt_mask[2:4, 2:4] = True

    # Prediction: 2x2 square shifted by 1 pixel in X: rows 2..3, cols 3..4 (4 pixels)
    # Intersection = 2 pixels (cols 3..3, rows 2..3)
    # Union = 6 pixels
    pred_mask = np.zeros((H, W), dtype=bool)
    pred_mask[2:4, 3:5] = True

    # Expected:
    # IoU = 2 / 6 = 1/3
    # Dice = 2 * 2 / (4 + 4) = 4/8 = 0.5
    # Precision = 2 / 4 = 0.5
    # Recall = 2 / 4 = 0.5
    gt = GroundTruth(
        center_x_mm=2.5 * dx,
        center_y_mm=2.5 * dy,
        depth_mm=0.5,
        diameter_mm=2.0 * math.sqrt(4.0 * dx * dy / math.pi),
        thickness_mm=0.5,
        material_name="slag",
        area_mm2=4.0 * dx * dy,
        volume_mm3=4.0 * dx * dy * 0.5,
        has_defect=True
    )

    from lfmt.detection import DetectionResult
    det_res = DetectionResult(
        predicted_mask=pred_mask,
        is_detected=True,
        centroid_px=(3.5, 2.5),
        centroid_mm=(3.5 * dx, 2.5 * dy),
        equivalent_diameter_mm=gt.diameter_mm,
        area_px=4,
        area_mm2=gt.area_mm2,
        threshold_value=0.5,
        threshold_method="test",
        bounding_box_px=(2, 3, 3, 4),
        confidence_score=1.0,
        runtime_seconds=0.01,
        metadata={}
    )

    score_map = pred_mask.astype(float)
    metrics = compute_metrics("Test", det_res, gt, gt_mask, score_map, runtime_seconds=0.01, fov_mm=(fov_x_mm, fov_y_mm))

    assert math.isclose(metrics.iou, 1.0 / 3.0, rel_tol=1e-4)
    assert math.isclose(metrics.dice, 0.5, rel_tol=1e-4)
    assert math.isclose(metrics.precision, 0.5, rel_tol=1e-4)
    assert math.isclose(metrics.recall, 0.5, rel_tol=1e-4)
    # 1 pixel shift in X
    assert math.isclose(metrics.localization_error_px, 1.0, rel_tol=1e-4)
    assert math.isclose(metrics.localization_error_mm, 1.0 * dx, rel_tol=1e-4)
