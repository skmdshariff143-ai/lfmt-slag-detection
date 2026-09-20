"""
Defect Segmentation and Spatial Localization Pipeline.

Provides automated thresholding (Otsu, Percentile, Sigma-clipping),
morphological filtering, connected-component isolation, centroid estimation,
and physical dimension conversion (pixels to millimeters).
"""

from __future__ import annotations
import math
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
import numpy as np
from scipy.ndimage import label, binary_opening, binary_closing, center_of_mass, generate_binary_structure


@dataclass
class DetectionResult:
    """
    Segmentation and Localization Output.

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


def compute_otsu_threshold(image_2d: np.ndarray) -> float:
    """Compute Otsu's optimal global binarization threshold."""
    img_flat = image_2d.ravel()
    # Normalize to [0, 255] for histogram
    img_min, img_max = np.min(img_flat), np.max(img_flat)
    if (img_max - img_min) < 1e-12:
        return float(img_min)

    hist, bin_edges = np.histogram(img_flat, bins=256, range=(img_min, img_max), density=True)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

    weight1 = np.cumsum(hist)
    weight2 = np.cumsum(hist[::-1])[::-1]

    mean1 = np.cumsum(hist * bin_centers) / (weight1 + 1e-12)
    mean2 = (np.cumsum((hist * bin_centers)[::-1]) / (weight2[::-1] + 1e-12))[::-1]

    # Inter-class variance: w1 * w2 * (mu1 - mu2)^2
    variance = weight1[:-1] * weight2[1:] * (mean1[:-1] - mean2[1:]) ** 2
    idx_max = np.argmax(variance)
    return float(bin_centers[idx_max])


class DefectDetector:
    """
    Thermal Anomaly Segmentation and Localization Engine.
    """

    def __init__(
        self,
        threshold_method: str = "adaptive_otsu",
        morphology_kernel_size: int = 3,
        min_area_px: int = 3,
        percentile_val: float = 95.0,
        sigma_multiplier: float = 2.0
    ):
        self.threshold_method = threshold_method
        self.morphology_kernel_size = morphology_kernel_size
        self.min_area_px = min_area_px
        self.percentile_val = percentile_val
        self.sigma_multiplier = sigma_multiplier

    def detect(
        self,
        score_map: np.ndarray,
        fov_mm: Tuple[float, float] = (100.0, 70.0)
    ) -> DetectionResult:
        """
        Execute segmentation and feature extraction on 2D score map.

        Args:
            score_map: 2D array (H, W).
            fov_mm: Physical plate field of view (length_mm, width_mm) -> (FOV_x, FOV_y).

        Returns:
            DetectionResult instance.
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
        struct = generate_binary_structure(2, 2)
        binary_cleaned = binary_opening(binary_raw, structure=struct)
        binary_cleaned = binary_closing(binary_cleaned, structure=struct)

        # 4. Connected components
        labeled_array, num_features = label(binary_cleaned, structure=struct)

        # Find largest / most significant component
        best_component_mask = np.zeros((H, W), dtype=bool)
        is_detected = False
        centroid_px = (W / 2.0, H / 2.0)
        centroid_mm = (fov_x_mm / 2.0, fov_y_mm / 2.0)
        area_px = 0
        area_mm2 = 0.0
        equiv_diam_mm = 0.0
        bbox_px = (0, 0, H, W)
        confidence = 0.0

        if num_features > 0:
            component_sizes = [np.sum(labeled_array == i) for i in range(1, num_features + 1)]
            largest_comp_idx = int(np.argmax(component_sizes)) + 1
            area_px = int(component_sizes[largest_comp_idx - 1])

            if area_px >= self.min_area_px:
                is_detected = True
                best_component_mask = (labeled_array == largest_comp_idx)
                
                # Center of mass (row, col) = (y, x)
                cy, cx = center_of_mass(best_component_mask)
                centroid_px = (float(cx), float(cy))
                centroid_mm = (float(cx * dx_mm_px), float(cy * dy_mm_px))

                area_mm2 = float(area_px * pixel_area_mm2)
                equiv_diam_mm = 2.0 * math.sqrt(area_mm2 / math.pi)

                # Bounding box
                rows, cols = np.where(best_component_mask)
                bbox_px = (int(np.min(rows)), int(np.min(cols)), int(np.max(rows)), int(np.max(cols)))

                # Confidence: ratio of inside intensity to background
                mu_in = np.mean(norm_map[best_component_mask])
                mu_out = np.mean(norm_map[~best_component_mask]) if np.any(~best_component_mask) else 0.0
                confidence = float(max(0.0, (mu_in - mu_out) / (mu_out + 1e-6)))

        elapsed = time.perf_counter() - start_t

        metadata = {
            "num_connected_components": num_features,
            "threshold_method": self.threshold_method,
            "threshold_value": thresh,
            "dx_mm_px": dx_mm_px,
            "dy_mm_px": dy_mm_px,
            "runtime_s": elapsed,
        }

        return DetectionResult(
            predicted_mask=best_component_mask,
            is_detected=is_detected,
            centroid_px=centroid_px,
            centroid_mm=centroid_mm,
            equivalent_diameter_mm=equiv_diam_mm,
            area_px=area_px,
            area_mm2=area_mm2,
            threshold_value=thresh,
            threshold_method=self.threshold_method,
            bounding_box_px=bbox_px,
            confidence_score=confidence,
            runtime_seconds=elapsed,
            metadata=metadata
        )
