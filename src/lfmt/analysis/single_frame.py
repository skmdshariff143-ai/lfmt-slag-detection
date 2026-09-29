"""
Single-Frame Spatial Thermographic Analysis Module.

Provides 2D spatial anomaly enhancement, gradient magnitude, Laplacian filtering,
local entropy mapping, and candidate isolation for static single-frame thermal uploads.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Tuple, Optional
import numpy as np
from scipy.ndimage import sobel, laplace, uniform_filter, gaussian_filter

from lfmt.detection import MultiDefectDetector, MultiDetectionResult


@dataclass
class SingleFrameSpatialResult:
    """Output of spatial analysis on a static single thermal frame."""
    spatial_contrast_map: np.ndarray
    gradient_magnitude_map: np.ndarray
    laplacian_edge_map: np.ndarray
    local_variance_map: np.ndarray
    detection_result: MultiDetectionResult
    peak_anomaly_contrast: float
    runtime_seconds: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class SingleFrameSpatialAnalyzer:
    """Analyzes a 2D thermal frame without temporal information."""

    def __init__(
        self,
        blur_sigma_px: float = 1.0,
        local_window_size: int = 15,
        min_area_px: int = 4,
        min_confidence: float = 0.05
    ):
        self.blur_sigma_px = blur_sigma_px
        self.local_window_size = local_window_size
        self.min_area_px = min_area_px
        self.min_confidence = min_confidence

    def process(
        self,
        image_2d: np.ndarray,
        fov_mm: Optional[Tuple[float, float]] = None
    ) -> SingleFrameSpatialResult:
        """
        Process single 2D thermal frame.

        Args:
            image_2d: 2D array of temperatures or normalized intensity (H, W).
            fov_mm: Optional (length_mm, width_mm).

        Returns:
            SingleFrameSpatialResult container.
        """
        start_t = time.perf_counter()
        img = image_2d.astype(np.float64)
        H, W = img.shape
        fov = fov_mm or (100.0, 70.0)

        # 1. Local background estimation via uniform filter
        bg = uniform_filter(img, size=self.local_window_size, mode="reflect")
        spatial_contrast = img - bg

        # 2. Gradient magnitude & Laplacian
        smoothed = gaussian_filter(img, sigma=self.blur_sigma_px)
        gx = sobel(smoothed, axis=1)
        gy = sobel(smoothed, axis=0)
        grad_mag = np.hypot(gx, gy)
        lap_map = np.abs(laplace(smoothed))

        # 3. Local variance
        img_sq = uniform_filter(img ** 2, size=self.local_window_size, mode="reflect")
        local_var = np.maximum(0.0, img_sq - bg ** 2)

        # 4. Multi-Defect Detection on spatial contrast map
        detector = MultiDefectDetector(
            threshold_method="adaptive_otsu",
            morphology_kernel_size=3,
            min_area_px=self.min_area_px,
            min_confidence=self.min_confidence
        )
        det_result = detector.detect_all(spatial_contrast, fov_mm=fov)

        peak_contrast = float(np.max(np.abs(spatial_contrast)))
        elapsed = time.perf_counter() - start_t

        return SingleFrameSpatialResult(
            spatial_contrast_map=spatial_contrast,
            gradient_magnitude_map=grad_mag,
            laplacian_edge_map=lap_map,
            local_variance_map=local_var,
            detection_result=det_result,
            peak_anomaly_contrast=round(peak_contrast, 4),
            runtime_seconds=round(elapsed, 4),
            metadata={
                "local_window_size": self.local_window_size,
                "blur_sigma_px": self.blur_sigma_px,
                "n_candidates_found": det_result.n_candidates
            }
        )
