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
    localization_error_detected_mm: float  # Only for successful detections (NaN if not detected)
    localization_error_all_mm: float       # For any candidate produced (NaN if no candidate)
    localization_error_mm: float           # Alias to localization_error_detected_mm for backward compatibility
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
    candidate_detected: bool               # Blind detector produced a candidate anomaly
    is_detected: bool                      # Evaluation success (candidate satisfies GT overlap & proximity)
    is_false_positive: bool                # Blind detector flagged anomaly on healthy control
    runtime_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method_name": self.method_name,
            "iou": round(self.iou, 4) if not math.isnan(self.iou) else None,
            "dice": round(self.dice, 4) if not math.isnan(self.dice) else None,
            "precision": round(self.precision, 4) if not math.isnan(self.precision) else None,
            "recall": round(self.recall, 4) if not math.isnan(self.recall) else None,
            "localization_error_detected_mm": round(self.localization_error_detected_mm, 3) if not math.isnan(self.localization_error_detected_mm) else None,
            "localization_error_all_mm": round(self.localization_error_all_mm, 3) if not math.isnan(self.localization_error_all_mm) else None,
            "localization_error_mm": round(self.localization_error_mm, 3) if not math.isnan(self.localization_error_mm) else None,
            "localization_error_px": round(self.localization_error_px, 3) if not math.isnan(self.localization_error_px) else None,
            "true_centroid_mm": [round(c, 2) for c in self.true_centroid_mm] if not any(math.isnan(c) for c in self.true_centroid_mm) else None,
            "predicted_centroid_mm": [round(c, 2) for c in self.predicted_centroid_mm] if not any(math.isnan(c) for c in self.predicted_centroid_mm) else None,
            "diameter_error_mm": round(self.diameter_error_mm, 3) if not math.isnan(self.diameter_error_mm) else None,
            "true_diameter_mm": round(self.true_diameter_mm, 2),
            "predicted_diameter_mm": round(self.predicted_diameter_mm, 2) if not math.isnan(self.predicted_diameter_mm) else None,
            "area_error_mm2": round(self.area_error_mm2, 2) if not math.isnan(self.area_error_mm2) else None,
            "true_area_mm2": round(self.true_area_mm2, 2),
            "predicted_area_mm2": round(self.predicted_area_mm2, 2) if not math.isnan(self.predicted_area_mm2) else None,
            "cnr": round(self.cnr, 3),
            "defect_contrast": round(self.defect_contrast, 4),
            "candidate_detected": self.candidate_detected,
            "is_detected": self.is_detected,
            "is_false_positive": self.is_false_positive,
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

    intersection = int(np.sum(pred_mask & gt_mask))
    union = int(np.sum(pred_mask | gt_mask))
    pred_sum = int(np.sum(pred_mask))
    gt_sum = int(np.sum(gt_mask))

    has_candidate = bool(detection.is_detected and pred_sum >= 3)
    is_defective = bool(gt_sum > 0)

    # 1. Overlap metrics
    if is_defective:
        iou = float(intersection) / float(union) if union > 0 else 0.0
        dice = (2.0 * float(intersection)) / float(pred_sum + gt_sum) if (pred_sum + gt_sum) > 0 else 0.0
        precision = float(intersection) / float(pred_sum) if pred_sum > 0 else 0.0
        recall = float(intersection) / float(gt_sum) if gt_sum > 0 else 0.0
    else:
        # Healthy specimen: 1.0 if clean (true negative), 0.0 if false alarm
        iou = 1.0 if not has_candidate else 0.0
        dice = 1.0 if not has_candidate else 0.0
        precision = 1.0 if not has_candidate else 0.0
        recall = 1.0

    # 2. Centroid & Localization error
    gt_x_mm = ground_truth.center_x_mm if is_defective else float("nan")
    gt_y_mm = ground_truth.center_y_mm if is_defective else float("nan")
    pred_x_mm, pred_y_mm = detection.centroid_mm

    if has_candidate and is_defective and not (math.isnan(pred_x_mm) or math.isnan(pred_y_mm)):
        loc_err_all_mm = math.sqrt((pred_x_mm - gt_x_mm) ** 2 + (pred_y_mm - gt_y_mm) ** 2)
        loc_err_all_px = math.sqrt(((pred_x_mm - gt_x_mm) / dx_mm_px) ** 2 + ((pred_y_mm - gt_y_mm) / dy_mm_px) ** 2)
    else:
        loc_err_all_mm = float("nan")
        loc_err_all_px = float("nan")

    # 3. Geometric errors
    true_diam_mm = ground_truth.diameter_mm if is_defective else 0.0
    pred_diam_mm = detection.equivalent_diameter_mm if has_candidate else float("nan")
    diam_err_mm = abs(pred_diam_mm - true_diam_mm) if (has_candidate and is_defective) else float("nan")

    true_area_mm2 = ground_truth.area_mm2 if is_defective else 0.0
    pred_area_mm2 = detection.area_mm2 if has_candidate else float("nan")
    area_err_mm2 = abs(pred_area_mm2 - true_area_mm2) if (has_candidate and is_defective) else float("nan")

    # 4. Contrast and CNR on score map (Evaluation metric using ground truth)
    if is_defective and np.any(gt_mask) and np.any(~gt_mask):
        mu_defect = float(np.mean(score_map[gt_mask]))
        mu_sound = float(np.mean(score_map[~gt_mask]))
        var_defect = float(np.var(score_map[gt_mask]))
        var_sound = float(np.var(score_map[~gt_mask]))

        defect_contrast = float(abs(mu_defect - mu_sound))
        denom = math.sqrt(var_defect + var_sound)
        cnr = float(defect_contrast / denom) if denom > 1e-12 else 0.0
    else:
        defect_contrast = 0.0
        cnr = 0.0

    # 5. Defect detection success criteria (Frozen Protocol):
    # A detection is a true success IF AND ONLY IF:
    # - It is a defective plate (gt_sum > 0)
    # - Blind detector isolated a candidate (has_candidate == True)
    # - Spatial overlap with true defect (intersection > 0)
    # - Centroid error within max(R_true, 5.0 mm)
    if is_defective:
        is_valid_detection = bool(
            has_candidate and
            (intersection > 0) and
            (not math.isnan(loc_err_all_mm)) and
            (loc_err_all_mm <= max(true_diam_mm / 2.0, 5.0))
        )
        is_false_positive = False
    else:
        # Healthy specimen (0 inclusions):
        # A false positive occurs if blind detector flagged an anomaly
        is_valid_detection = False
        is_false_positive = has_candidate

    loc_err_detected_mm = loc_err_all_mm if is_valid_detection else float("nan")
    loc_err_detected_px = loc_err_all_px if is_valid_detection else float("nan")

    return EvaluationMetrics(
        method_name=method_name,
        iou=iou,
        dice=dice,
        precision=precision,
        recall=recall,
        localization_error_detected_mm=loc_err_detected_mm,
        localization_error_all_mm=loc_err_all_mm,
        localization_error_mm=loc_err_detected_mm,
        localization_error_px=loc_err_detected_px,
        true_centroid_mm=(gt_x_mm, gt_y_mm),
        predicted_centroid_mm=(pred_x_mm, pred_y_mm),
        diameter_error_mm=diam_err_mm,
        true_diameter_mm=true_diam_mm,
        predicted_diameter_mm=pred_diam_mm,
        area_error_mm2=area_err_mm2,
        true_area_mm2=true_area_mm2,
        predicted_area_mm2=pred_area_mm2,
        cnr=cnr,
        defect_contrast=defect_contrast,
        candidate_detected=has_candidate,
        is_detected=is_valid_detection,
        is_false_positive=is_false_positive,
        runtime_seconds=runtime_seconds
    )
