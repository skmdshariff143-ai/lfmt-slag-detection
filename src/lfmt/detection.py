"""
Defect Segmentation and Spatial Localization Pipeline.

Provides automated thresholding (Otsu, Percentile, Sigma-clipping),
morphological filtering, connected-component isolation, centroid estimation,
and physical dimension conversion (pixels to millimeters).
"""

from __future__ import annotations
import math
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Tuple, List
import numpy as np
from scipy.ndimage import label, binary_opening, binary_closing, center_of_mass, generate_binary_structure
from scipy.optimize import linear_sum_assignment


@dataclass
class DetectionResult:
    """
    Segmentation and Localization Output for a single (primary) defect.

    Attributes:
        predicted_mask: 2D boolean array (H, W) of isolated defect region.
        is_detected: Boolean flag indicating if a valid defect anomaly was isolated.
        centroid_px: (x_px, y_px) pixel coordinates of defect centroid.
        centroid_mm: (x_mm, y_mm) physical coordinates of defect centroid in millimeters.
        equivalent_diameter_mm: Estimated diameter of defect disc in millimeters.
        area_px: Detected defect area in pixel count.
        area_mm2: Detected defect area in square millimeters.
        threshold_value: Numerical threshold used for binarization.
        threshold_method: Strategy used ("adaptive_otsu", "percentile", "sigma_clipping").
        bounding_box_px: (ymin, xmin, ymax, xmax) bounding box in pixels.
        confidence_score: Contrast-to-background detection confidence metric.
        runtime_seconds: Execution time in seconds.
        metadata: Dictionary of auxiliary metadata.
    """
    predicted_mask: np.ndarray
    is_detected: bool
    centroid_px: Tuple[float, float]
    centroid_mm: Tuple[float, float]
    equivalent_diameter_mm: float
    area_px: int
    area_mm2: float
    threshold_value: float
    threshold_method: str
    bounding_box_px: Tuple[int, int, int, int]
    confidence_score: float
    runtime_seconds: float
    metadata: Dict[str, Any]


@dataclass
class DefectCandidate:
    """Individual candidate anomaly isolated during multi-defect detection."""
    component_id: int
    mask: np.ndarray
    centroid_px: Tuple[float, float]
    centroid_mm: Tuple[float, float]
    equivalent_diameter_mm: float
    area_px: int
    area_mm2: float
    bounding_box_px: Tuple[int, int, int, int]
    confidence_score: float
    peak_intensity: float
    mean_intensity: float


@dataclass
class MultiDetectionResult:
    """Result containing all segmented defect candidates."""
    candidates: List[DefectCandidate]
    combined_mask: np.ndarray
    n_candidates: int
    threshold_value: float
    threshold_method: str
    runtime_seconds: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_detected(self) -> bool:
        return self.n_candidates > 0

    def to_single_result(self) -> DetectionResult:
        """Convert multi-defect result to primary DetectionResult for backward compatibility."""
        if self.n_candidates > 0:
            top = self.candidates[0]
            return DetectionResult(
                predicted_mask=top.mask,
                is_detected=True,
                centroid_px=top.centroid_px,
                centroid_mm=top.centroid_mm,
                equivalent_diameter_mm=top.equivalent_diameter_mm,
                area_px=top.area_px,
                area_mm2=top.area_mm2,
                threshold_value=self.threshold_value,
                threshold_method=self.threshold_method,
                bounding_box_px=top.bounding_box_px,
                confidence_score=top.confidence_score,
                runtime_seconds=self.runtime_seconds,
                metadata=self.metadata
            )
        H, W = self.combined_mask.shape
        return DetectionResult(
            predicted_mask=np.zeros((H, W), dtype=bool),
            is_detected=False,
            centroid_px=(float("nan"), float("nan")),
            centroid_mm=(float("nan"), float("nan")),
            equivalent_diameter_mm=float("nan"),
            area_px=0,
            area_mm2=0.0,
            threshold_value=self.threshold_value,
            threshold_method=self.threshold_method,
            bounding_box_px=(0, 0, 0, 0),
            confidence_score=0.0,
            runtime_seconds=self.runtime_seconds,
            metadata=self.metadata
        )


def compute_otsu_threshold(image_2d: np.ndarray) -> float:
    """Compute Otsu's optimal global binarization threshold."""
    img_flat = image_2d.ravel()
    img_min, img_max = np.min(img_flat), np.max(img_flat)
    if (img_max - img_min) < 1e-12:
        return float(img_min)

    hist, bin_edges = np.histogram(img_flat, bins=256, range=(img_min, img_max), density=True)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

    weight1 = np.cumsum(hist)
    weight2 = np.cumsum(hist[::-1])[::-1]

    mean1 = np.cumsum(hist * bin_centers) / (weight1 + 1e-12)
    mean2 = (np.cumsum((hist * bin_centers)[::-1]) / (weight2[::-1] + 1e-12))[::-1]

    variance = weight1[:-1] * weight2[1:] * (mean1[:-1] - mean2[1:]) ** 2
    idx_max = np.argmax(variance)
    return float(bin_centers[idx_max])


class MultiDefectDetector:
    """
    High-Fidelity Multi-Defect Segmentation and Candidate Ranking Engine.
    """

    def __init__(
        self,
        threshold_method: str = "adaptive_otsu",
        morphology_kernel_size: int = 3,
        min_area_px: int = 3,
        max_candidates: int = 10,
        percentile_val: float = 95.0,
        sigma_multiplier: float = 2.0,
        min_confidence: float = 0.05
    ):
        self.threshold_method = threshold_method
        self.morphology_kernel_size = morphology_kernel_size
        self.min_area_px = min_area_px
        self.max_candidates = max_candidates
        self.percentile_val = percentile_val
        self.sigma_multiplier = sigma_multiplier
        self.min_confidence = min_confidence

    def detect_all(
        self,
        score_map: np.ndarray,
        fov_mm: Tuple[float, float] = (100.0, 70.0)
    ) -> MultiDetectionResult:
        """
        Segment all candidate thermal anomalies from score map.
        """
        start_t = time.perf_counter()
        H, W = score_map.shape
        fov_x_mm, fov_y_mm = fov_mm
        dx_mm_px = fov_x_mm / max(1, W - 1)
        dy_mm_px = fov_y_mm / max(1, H - 1)
        pixel_area_mm2 = dx_mm_px * dy_mm_px

        # 1. Normalize map to [0, 1]
        s_min, s_max = np.min(score_map), np.max(score_map)
        if (s_max - s_min) > 1e-12:
            norm_map = (score_map - s_min) / (s_max - s_min)
        else:
            norm_map = np.zeros_like(score_map)

        # 2. Thresholding
        if self.threshold_method == "percentile":
            thresh = float(np.percentile(norm_map, self.percentile_val))
        elif self.threshold_method == "sigma_clipping":
            mu, sigma = float(np.mean(norm_map)), float(np.std(norm_map))
            thresh = mu + self.sigma_multiplier * sigma
        else:  # "adaptive_otsu"
            thresh = compute_otsu_threshold(norm_map)

        binary_raw = norm_map >= thresh

        # 3. Morphological filtering
        k_size = self.morphology_kernel_size
        if k_size <= 1:
            binary_cleaned = binary_raw
            struct = generate_binary_structure(2, 2)
        elif k_size == 3:
            struct = generate_binary_structure(2, 2)
            binary_cleaned = binary_opening(binary_raw, structure=struct)
            binary_cleaned = binary_closing(binary_cleaned, structure=struct)
        else:
            struct = np.ones((k_size, k_size), dtype=bool)
            binary_cleaned = binary_opening(binary_raw, structure=struct)
            binary_cleaned = binary_closing(binary_cleaned, structure=struct)

        # 4. Connected components
        labeled_array, num_features = label(binary_cleaned, structure=struct)

        candidates: List[DefectCandidate] = []
        combined_mask = np.zeros((H, W), dtype=bool)

        if num_features > 0:
            for comp_id in range(1, num_features + 1):
                comp_mask = (labeled_array == comp_id)
                area_px = int(np.sum(comp_mask))

                if area_px < self.min_area_px:
                    continue

                # Centroid
                cy, cx = center_of_mass(comp_mask)
                centroid_px = (float(cx), float(cy))
                centroid_mm = (float(cx * dx_mm_px), float(cy * dy_mm_px))

                area_mm2 = float(area_px * pixel_area_mm2)
                equiv_diam_mm = 2.0 * math.sqrt(area_mm2 / math.pi)

                # Bounding box
                rows, cols = np.where(comp_mask)
                bbox_px = (int(np.min(rows)), int(np.min(cols)), int(np.max(rows)), int(np.max(cols)))

                # Intensity & Confidence
                mu_in = float(np.mean(norm_map[comp_mask]))
                peak_in = float(np.max(norm_map[comp_mask]))
                mu_out = float(np.mean(norm_map[~comp_mask])) if np.any(~comp_mask) else 0.0
                conf = float(max(0.0, (mu_in - mu_out) / (mu_out + 1e-6)))

                if conf < self.min_confidence:
                    continue

                candidate = DefectCandidate(
                    component_id=comp_id,
                    mask=comp_mask,
                    centroid_px=centroid_px,
                    centroid_mm=centroid_mm,
                    equivalent_diameter_mm=equiv_diam_mm,
                    area_px=area_px,
                    area_mm2=area_mm2,
                    bounding_box_px=bbox_px,
                    confidence_score=conf,
                    peak_intensity=peak_in,
                    mean_intensity=mu_in
                )
                candidates.append(candidate)

            # Sort candidates by confidence * sqrt(area)
            candidates.sort(key=lambda c: c.confidence_score * math.sqrt(c.area_px), reverse=True)
            candidates = candidates[:self.max_candidates]

            for c in candidates:
                combined_mask |= c.mask

        elapsed = time.perf_counter() - start_t

        metadata = {
            "num_connected_components": num_features,
            "num_candidates_retained": len(candidates),
            "threshold_method": self.threshold_method,
            "threshold_value": thresh,
            "dx_mm_px": dx_mm_px,
            "dy_mm_px": dy_mm_px,
            "runtime_s": elapsed,
        }

        return MultiDetectionResult(
            candidates=candidates,
            combined_mask=combined_mask,
            n_candidates=len(candidates),
            threshold_value=thresh,
            threshold_method=self.threshold_method,
            runtime_seconds=elapsed,
            metadata=metadata
        )

    def detect(
        self,
        score_map: np.ndarray,
        fov_mm: Tuple[float, float] = (100.0, 70.0)
    ) -> DetectionResult:
        """Single-defect backward-compatible detect method."""
        multi_res = self.detect_all(score_map, fov_mm)
        return multi_res.to_single_result()


class DefectDetector(MultiDefectDetector):
    """
    Thermal Anomaly Segmentation and Localization Engine (V1 & V2 compatible).
    """
    pass


def match_defects_hungarian(
    gt_centroids_mm: List[Tuple[float, float]],
    pred_centroids_mm: List[Tuple[float, float]],
    max_distance_mm: float = 10.0
) -> Dict[str, Any]:
    """
    Perform Hungarian bipartite matching between ground truth defect centroids and predicted centroids.

    Returns:
        Dictionary containing matched pairs, unmatched GT, unmatched predictions,
        and object-level Precision, Recall, and F1-score.
    """
    n_gt = len(gt_centroids_mm)
    n_pred = len(pred_centroids_mm)

    if n_gt == 0 and n_pred == 0:
        return {
            "matched_pairs": [],
            "unmatched_gt": [],
            "unmatched_pred": [],
            "precision": 1.0,
            "recall": 1.0,
            "f1": 1.0,
            "mean_localization_error_mm": 0.0
        }

    if n_gt == 0:
        return {
            "matched_pairs": [],
            "unmatched_gt": [],
            "unmatched_pred": list(range(n_pred)),
            "precision": 0.0,
            "recall": 1.0,
            "f1": 0.0,
            "mean_localization_error_mm": float("nan")
        }

    if n_pred == 0:
        return {
            "matched_pairs": [],
            "unmatched_gt": list(range(n_gt)),
            "unmatched_pred": [],
            "precision": 1.0,
            "recall": 0.0,
            "f1": 0.0,
            "mean_localization_error_mm": float("nan")
        }

    cost_matrix = np.zeros((n_gt, n_pred), dtype=np.float64)
    for i, (gx, gy) in enumerate(gt_centroids_mm):
        for j, (px, py) in enumerate(pred_centroids_mm):
            cost_matrix[i, j] = math.sqrt((gx - px) ** 2 + (gy - py) ** 2)

    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    matched_pairs = []
    matched_gt = set()
    matched_pred = set()
    loc_errors = []

    for r, c in zip(row_ind, col_ind):
        dist = float(cost_matrix[r, c])
        if dist <= max_distance_mm:
            matched_pairs.append((r, c, dist))
            matched_gt.add(r)
            matched_pred.add(c)
            loc_errors.append(dist)

    unmatched_gt = [i for i in range(n_gt) if i not in matched_gt]
    unmatched_pred = [j for j in range(n_pred) if j not in matched_pred]

    tp = len(matched_pairs)
    fp = len(unmatched_pred)
    fn = len(unmatched_gt)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    mean_loc_err = float(np.mean(loc_errors)) if loc_errors else float("nan")

    return {
        "matched_pairs": matched_pairs,
        "unmatched_gt": unmatched_gt,
        "unmatched_pred": unmatched_pred,
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "mean_localization_error_mm": mean_loc_err
    }
