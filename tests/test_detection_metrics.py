"""Unit tests for defect detection, segmentation, and evaluation metrics."""

import pytest
import numpy as np
import math
from lfmt.detection import DefectDetector, compute_otsu_threshold
from lfmt.metrics import compute_metrics
from lfmt.simulation.base import GroundTruth


def test_otsu_threshold():
    # Synthetic bimodal distribution (sound background at 0.2, defect at 0.8)
    img = np.full((30, 30), 0.2)
    img[10:20, 10:20] = 0.8
    thresh = compute_otsu_threshold(img)
    assert 0.2 < thresh < 0.8


def test_defect_detector():
    H, W = 40, 40
    # Synthetic circular defect centered at (20, 20) with radius 5
    Y, X = np.ogrid[:H, :W]
    dist_sq = (Y - 20)**2 + (X - 20)**2
    score_map = np.exp(-dist_sq / (2 * 5**2))  # Gaussian peak

    detector = DefectDetector(threshold_method="adaptive_otsu", min_area_px=4)
    res = detector.detect(score_map, fov_mm=(100.0, 70.0))

    assert res.is_detected
    assert res.predicted_mask.shape == (H, W)
    # Centroid should be very close to (20, 20) in pixels
    assert abs(res.centroid_px[0] - 20) < 1.0
    assert abs(res.centroid_px[1] - 20) < 1.0


def test_compute_metrics():
    H, W = 50, 50
    gt_mask = np.zeros((H, W), dtype=bool)
    gt_mask[20:30, 20:30] = True

    gt = GroundTruth(
        center_x_mm=50.0,
        center_y_mm=35.0,
        depth_mm=0.6,
        diameter_mm=10.0,
        thickness_mm=0.5,
        material_name="slag",
        area_mm2=math.pi * 5.0**2,
        volume_mm3=math.pi * 5.0**2 * 0.5,
        has_defect=True
    )

    # Perfect prediction case
    score_map = gt_mask.astype(float)
    detector = DefectDetector(threshold_method="adaptive_otsu", min_area_px=1)
    det_res = detector.detect(score_map, fov_mm=(100.0, 70.0))

    # Overwrite centroid to exact match
    metrics = compute_metrics(
        method_name="PCT",
        detection=det_res,
        ground_truth=gt,
        ground_truth_mask=gt_mask,
        score_map=score_map,
        runtime_seconds=0.05,
        fov_mm=(100.0, 70.0)
    )

    assert metrics.dice > 0.8
    assert metrics.iou > 0.7
    assert metrics.is_detected
    assert metrics.runtime_seconds == 0.05
