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
    tier_a_detected: bool = False          # Tier A: Legacy V1 (overlap > 0, dist <= max(r, 5mm))
    tier_b_detected: bool = False          # Tier B: Moderate (IoU >= 0.10, dist <= max(r, 3mm))
    tier_c_detected: bool = False          # Tier C: Strict (IoU >= 0.25, dist <= r)
    tier_d_detected: bool = False          # Tier D: High-Precision (IoU >= 0.50, dist <= 0.5*r)
    roc_auc: Optional[float] = None
    pr_ap: Optional[float] = None

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
            "tier_a_detected": self.tier_a_detected,
            "tier_b_detected": self.tier_b_detected,
            "tier_c_detected": self.tier_c_detected,
            "tier_d_detected": self.tier_d_detected,
            "roc_auc": round(self.roc_auc, 4) if self.roc_auc is not None and not math.isnan(self.roc_auc) else None,
            "pr_ap": round(self.pr_ap, 4) if self.pr_ap is not None and not math.isnan(self.pr_ap) else None,
            "runtime_s": round(self.runtime_seconds, 4),
        }


def compute_roc_pr_curves(
    score_map: np.ndarray,
    ground_truth_mask: np.ndarray,
    n_thresholds: int = 100
) -> Dict[str, Any]:
    """
    Compute pixel-level ROC and Precision-Recall (PR) curves across score thresholds.

    Args:
        score_map: 2D continuous score map (H, W).
        ground_truth_mask: 2D boolean mask (H, W).
        n_thresholds: Number of evaluation thresholds.

    Returns:
        Dictionary containing thresholds, fpr, tpr, precision, recall, auc_roc, and average_precision.
    """
    s_min, s_max = float(np.min(score_map)), float(np.max(score_map))
    if (s_max - s_min) > 1e-12:
        norm_scores = (score_map - s_min) / (s_max - s_min)
    else:
        norm_scores = np.zeros_like(score_map)

    gt_flat = ground_truth_mask.ravel().astype(bool)
    n_pos = int(np.sum(gt_flat))
    n_neg = int(len(gt_flat) - n_pos)

    thresholds = np.linspace(0.0, 1.0, n_thresholds)
    tpr_list = []
    fpr_list = []
    prec_list = []
    rec_list = []

    if n_pos == 0:
        return {
            "thresholds": thresholds.tolist(),
            "fpr": [0.0] * n_thresholds,
            "tpr": [0.0] * n_thresholds,
            "precision": [0.0] * n_thresholds,
            "recall": [0.0] * n_thresholds,
            "auc_roc": 0.0,
            "average_precision": 0.0
        }

    for th in thresholds:
        pred_pos = norm_scores.ravel() >= th
        tp = int(np.sum(pred_pos & gt_flat))
        fp = int(np.sum(pred_pos & ~gt_flat))
        _fn = n_pos - tp
        _tn = n_neg - fp

        tpr = tp / n_pos if n_pos > 0 else 0.0
        fpr = fp / n_neg if n_neg > 0 else 0.0
        prec = tp / (tp + fp) if (tp + fp) > 0 else 1.0

        tpr_list.append(tpr)
        fpr_list.append(fpr)
        prec_list.append(prec)
        rec_list.append(tpr)

    # Sort by FPR ascending for ROC AUC calculation
    fpr_arr = np.array(fpr_list)
    tpr_arr = np.array(tpr_list)
    sort_idx = np.argsort(fpr_arr)
    sorted_fpr = fpr_arr[sort_idx]
    sorted_tpr = tpr_arr[sort_idx]

    try:
        auc_roc = float(np.trapezoid(sorted_tpr, sorted_fpr)) if hasattr(np, "trapezoid") else float(np.trapz(sorted_tpr, sorted_fpr))
    except Exception:
        auc_roc = 0.5

    # Average Precision from PR curve
    rec_arr = np.array(rec_list)
    prec_arr = np.array(prec_list)
    pr_sort_idx = np.argsort(rec_arr)
    sorted_rec = rec_arr[pr_sort_idx]
    sorted_prec = prec_arr[pr_sort_idx]
    try:
        ap = float(np.trapezoid(sorted_prec, sorted_rec)) if hasattr(np, "trapezoid") else float(np.trapz(sorted_prec, sorted_rec))
    except Exception:
        ap = float(np.mean(prec_arr))

    return {
        "thresholds": thresholds.tolist(),
        "fpr": [float(x) for x in fpr_list],
        "tpr": [float(x) for x in tpr_list],
        "precision": [float(x) for x in prec_list],
        "recall": [float(x) for x in rec_list],
        "auc_roc": float(np.clip(auc_roc, 0.0, 1.0)),
        "average_precision": float(np.clip(ap, 0.0, 1.0))
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
    Compute comprehensive scientific NDT evaluation metrics with multi-tier grading.

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
    true_radius_mm = true_diam_mm / 2.0
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

    # 5. Defect detection tiered success criteria:
    # Tier A (Legacy V1 / Baseline): overlap > 0 and centroid error <= max(R_true, 5.0 mm)
    # Tier B (Moderate): IoU >= 0.10 and centroid error <= max(R_true, 3.0 mm)
    # Tier C (Strict): IoU >= 0.25 and centroid error <= R_true
    # Tier D (High-Precision): IoU >= 0.50 and centroid error <= 0.5 * R_true
    if is_defective:
        has_valid_loc = (not math.isnan(loc_err_all_mm))
        tier_a = bool(has_candidate and (intersection > 0) and has_valid_loc and (loc_err_all_mm <= max(true_radius_mm, 5.0)))
        tier_b = bool(has_candidate and (iou >= 0.10) and has_valid_loc and (loc_err_all_mm <= max(true_radius_mm, 3.0)))
        tier_c = bool(has_candidate and (iou >= 0.25) and has_valid_loc and (loc_err_all_mm <= max(true_radius_mm, 1.0)))
        tier_d = bool(has_candidate and (iou >= 0.50) and has_valid_loc and (loc_err_all_mm <= max(0.5 * true_radius_mm, 0.5)))
        is_valid_detection = tier_a
        is_false_positive = False
    else:
        # Healthy specimen (0 inclusions)
        tier_a = False
        tier_b = False
        tier_c = False
        tier_d = False
        is_valid_detection = False
        is_false_positive = has_candidate

    loc_err_detected_mm = loc_err_all_mm if is_valid_detection else float("nan")
    loc_err_detected_px = loc_err_all_px if is_valid_detection else float("nan")

    # ROC / PR metrics on score map
    roc_metrics = compute_roc_pr_curves(score_map, gt_mask, n_thresholds=50) if is_defective else None
    roc_auc = roc_metrics["auc_roc"] if roc_metrics is not None else None
    pr_ap = roc_metrics["average_precision"] if roc_metrics is not None else None

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
        runtime_seconds=runtime_seconds,
        tier_a_detected=tier_a,
        tier_b_detected=tier_b,
        tier_c_detected=tier_c,
        tier_d_detected=tier_d,
        roc_auc=roc_auc,
        pr_ap=pr_ap
    )
