"""
Quantitative Performance Evaluation Metrics for NDT Defect Characterization.

Computes:
- Intersection over Union (IoU / Jaccard Index)
- Dice Similarity Coefficient (F1-score)
- Precision & Recall
- Localization Error (Euclidean distance in mm and pixels)
- Equivalent Diameter & Area Estimation Errors
- Contrast-to-Noise Ratio (CNR) & Signal-to-Noise Ratio (SNR)
- Binary Detection Success Rate
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
import numpy as np

from lfmt.detection import DetectionResult
from lfmt.simulation.base import GroundTruth


@dataclass
class EvaluationMetrics:
    """
    Complete quantitative metrics suite for a detection method.
    """
    method_name: str
    iou: float
    dice: float
    precision: float
    recall: float
    localization_error_mm: float
    localization_error_px: float
    true_centroid_mm: Tuple[float, float]
    predicted_centroid_mm: Tuple[float, float]
    diameter_error_mm: float
    true_diameter_mm: float
    predicted_diameter_mm: float
    area_error_mm2: float
    true_area_mm2: float
    predicted_area_mm2: float
    cnr: float
    defect_contrast: float
    is_detected: bool
    runtime_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method_name": self.method_name,
            "iou": round(self.iou, 4),
            "dice": round(self.dice, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "localization_error_mm": round(self.localization_error_mm, 3),
            "localization_error_px": round(self.localization_error_px, 3),
            "true_centroid_mm": [round(c, 2) for c in self.true_centroid_mm],
            "predicted_centroid_mm": [round(c, 2) for c in self.predicted_centroid_mm],
            "diameter_error_mm": round(self.diameter_error_mm, 3),
            "true_diameter_mm": round(self.true_diameter_mm, 2),
            "predicted_diameter_mm": round(self.predicted_diameter_mm, 2),
            "area_error_mm2": round(self.area_error_mm2, 2),
            "true_area_mm2": round(self.true_area_mm2, 2),
            "predicted_area_mm2": round(self.predicted_area_mm2, 2),
            "cnr": round(self.cnr, 3),
            "defect_contrast": round(self.defect_contrast, 4),
            "is_detected": self.is_detected,
            "runtime_s": round(self.runtime_seconds, 4),
        }


def compute_metrics(
    method_name: str,
    detection: DetectionResult,
    ground_truth: GroundTruth,
    ground_truth_mask: np.ndarray,
    score_map: np.ndarray,
    runtime_seconds: float = 0.0,
    fov_mm: Tuple[float, float] = (100.0, 70.0)
) -> EvaluationMetrics:
    """
    Compute comprehensive scientific NDT evaluation metrics.

    Args:
        method_name: Algorithm label ("Raw Contrast", "Matched Filter", "PCT", "SPCT", "RPT").
        detection: DetectionResult from DefectDetector.
        ground_truth: GroundTruth defect object.
        ground_truth_mask: 2D boolean array (H, W).
        score_map: 2D processed score image (H, W).
        runtime_seconds: Total processing time in seconds.
        fov_mm: Plate dimensions (length_mm, width_mm).

    Returns:
        EvaluationMetrics dataclass instance.
    """
    pred_mask = detection.predicted_mask.astype(bool)
    gt_mask = ground_truth_mask.astype(bool)

    H, W = gt_mask.shape
    fov_x_mm, fov_y_mm = fov_mm
    dx_mm_px = fov_x_mm / max(1, W - 1)
    dy_mm_px = fov_y_mm / max(1, H - 1)

    # 1. Overlap metrics
    intersection = np.sum(pred_mask & gt_mask)
    union = np.sum(pred_mask | gt_mask)
    pred_sum = np.sum(pred_mask)
    gt_sum = np.sum(gt_mask)

    iou = float(intersection) / float(union) if union > 0 else (1.0 if (pred_sum == 0 and gt_sum == 0) else 0.0)
    dice = (2.0 * float(intersection)) / float(pred_sum + gt_sum) if (pred_sum + gt_sum) > 0 else (1.0 if (pred_sum == 0 and gt_sum == 0) else 0.0)
    precision = float(intersection) / float(pred_sum) if pred_sum > 0 else 0.0
    recall = float(intersection) / float(gt_sum) if gt_sum > 0 else 0.0

    # 2. Localization error
    gt_x_mm = ground_truth.center_x_mm
    gt_y_mm = ground_truth.center_y_mm
    pred_x_mm, pred_y_mm = detection.centroid_mm

    loc_err_mm = math.sqrt((pred_x_mm - gt_x_mm) ** 2 + (pred_y_mm - gt_y_mm) ** 2)
    loc_err_px = math.sqrt(((pred_x_mm - gt_x_mm) / dx_mm_px) ** 2 + ((pred_y_mm - gt_y_mm) / dy_mm_px) ** 2)

    # 3. Geometric errors
    true_diam_mm = ground_truth.diameter_mm
    pred_diam_mm = detection.equivalent_diameter_mm
    diam_err_mm = abs(pred_diam_mm - true_diam_mm)

    true_area_mm2 = ground_truth.area_mm2
    pred_area_mm2 = detection.area_mm2
    area_err_mm2 = abs(pred_area_mm2 - true_area_mm2)

    # 4. Contrast and CNR on score map
    if np.any(gt_mask) and np.any(~gt_mask):
        mu_defect = np.mean(score_map[gt_mask])
        mu_sound = np.mean(score_map[~gt_mask])
        var_defect = np.var(score_map[gt_mask])
        var_sound = np.var(score_map[~gt_mask])

        defect_contrast = float(abs(mu_defect - mu_sound))
        denom = math.sqrt(var_defect + var_sound)
        cnr = float(defect_contrast / denom) if denom > 1e-12 else 0.0
    else:
        defect_contrast = 0.0
        cnr = 0.0

    # Defect detection success criteria (Frozen Protocol):
    # 1. Defect anomaly isolated (is_detected == True, pred_sum >= 3)
    # 2. Spatial overlap (intersection > 0)
    # 3. Centroid localization within max(R_true, 5.0 mm)
    if gt_sum > 0:
        is_valid_detection = bool(
            detection.is_detected and
            (pred_sum >= 3) and
            (intersection > 0) and
            (loc_err_mm <= max(true_diam_mm / 2.0, 5.0))
        )
    else:
        # Healthy specimen (0 inclusions)
        is_valid_detection = False

    return EvaluationMetrics(
        method_name=method_name,
        iou=iou,
        dice=dice,
        precision=precision,
        recall=recall,
        localization_error_mm=loc_err_mm if gt_sum > 0 else 0.0,
        localization_error_px=loc_err_px if gt_sum > 0 else 0.0,
        true_centroid_mm=(gt_x_mm, gt_y_mm) if gt_sum > 0 else (0.0, 0.0),
        predicted_centroid_mm=(pred_x_mm, pred_y_mm),
        diameter_error_mm=diam_err_mm if gt_sum > 0 else float(pred_diam_mm),
        true_diameter_mm=true_diam_mm,
        predicted_diameter_mm=pred_diam_mm,
        area_error_mm2=area_err_mm2 if gt_sum > 0 else float(pred_area_mm2),
        true_area_mm2=true_area_mm2,
        predicted_area_mm2=pred_area_mm2,
        cnr=cnr,
        defect_contrast=defect_contrast,
        is_detected=is_valid_detection,
        runtime_seconds=runtime_seconds
    )
