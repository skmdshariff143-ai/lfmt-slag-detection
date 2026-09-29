"""
Universal Preprocessing Engine for Thermographic Sequences and Single Frames.

Handles:
- Missing value (NaN/Inf) replacement and spatial interpolation
- Zero-variance / dead-frame filtering
- Blind pre-heating baseline subtraction
- Optional spatial Gaussian smoothing
- Generation of detailed preprocessing manifests
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy.ndimage import gaussian_filter


@dataclass
class PreprocessingManifest:
    """Detailed record of all preprocessing transformations applied."""
    applied_steps: List[str] = field(default_factory=list)
    initial_shape: Tuple[int, ...] = (0,)
    final_shape: Tuple[int, ...] = (0,)
    baseline_subtracted: bool = False
    baseline_frame_index: Optional[int] = None
    baseline_mean_temperature_k: Optional[float] = None
    dead_frames_removed: int = 0
    nan_pixels_fixed: int = 0
    spatial_filter_applied: bool = False
    runtime_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "applied_steps": self.applied_steps,
            "initial_shape": list(self.initial_shape),
            "final_shape": list(self.final_shape),
            "baseline_subtracted": self.baseline_subtracted,
            "baseline_frame_index": self.baseline_frame_index,
            "baseline_mean_temperature_k": self.baseline_mean_temperature_k,
            "dead_frames_removed": self.dead_frames_removed,
            "nan_pixels_fixed": self.nan_pixels_fixed,
            "spatial_filter_applied": self.spatial_filter_applied,
            "runtime_seconds": round(self.runtime_seconds, 4),
            "metadata": self.metadata
        }


class UniversalPreprocessor:
    """Automated, non-destructive thermographic preprocessing pipeline."""

    @staticmethod
    def preprocess(
        cube_k: np.ndarray,
        time_vector: Optional[np.ndarray] = None,
        apply_baseline_subtraction: bool = True,
        smooth_sigma_px: float = 0.0
    ) -> Tuple[np.ndarray, Optional[np.ndarray], PreprocessingManifest]:
        """
        Preprocess 3D thermal sequence or 2D image.

        Args:
            cube_k: 3D array (n_frames, H, W) or 2D array (H, W).
            time_vector: Optional 1D time array.
            apply_baseline_subtraction: If True and n_frames >= 5, subtracts blind ambient offset.
            smooth_sigma_px: Spatial Gaussian blur sigma in pixels (0.0 = disabled).

        Returns:
            (processed_cube, processed_time_vector, manifest)
        """
        start_t = time.perf_counter()
        manifest = PreprocessingManifest(initial_shape=cube_k.shape)

        if cube_k.ndim == 2:
            cube_k = cube_k[np.newaxis, :, :]

        N_frames, H, W = cube_k.shape
        data = cube_k.astype(np.float64)

        # 1. Clean NaNs and Infs
        nan_mask = np.isnan(data)
        inf_mask = np.isinf(data)
        total_bad = int(nan_mask.sum() + inf_mask.sum())
        if total_bad > 0:
            manifest.nan_pixels_fixed = total_bad
            manifest.applied_steps.append(f"Fixed {total_bad} NaN/Inf values with median replacement.")
            med_val = float(np.nanmedian(data))
            data = np.nan_to_num(data, nan=med_val, posinf=med_val + 50.0, neginf=med_val - 50.0)

        # 2. Dead frame removal (only if N > 10)
        t_vec = time_vector.copy() if time_vector is not None else np.arange(N_frames, dtype=float)
        if N_frames > 10:
            spatial_stds = np.std(data, axis=(1, 2))
            valid_frames = spatial_stds >= 1e-6
            dead_count = int((~valid_frames).sum())
            if 0 < dead_count < N_frames - 2:
                data = data[valid_frames]
                t_vec = t_vec[valid_frames]
                manifest.dead_frames_removed = dead_count
                manifest.applied_steps.append(f"Removed {dead_count} flat/dead frames with zero spatial variance.")

        N_frames = data.shape[0]

        # 3. Blind Reference Baseline Subtraction
        # For sequence data, find baseline from initial pre-heating frames or minimum global mean
        if apply_baseline_subtraction and N_frames >= 5:
            # Find frame with minimum global surface temperature as baseline candidate
            mean_temporal = np.mean(data, axis=(1, 2))
            base_idx = int(np.argmin(mean_temporal[:max(1, N_frames // 4)]))
            # Average over small window around baseline frame
            window_start = max(0, base_idx - 1)
            window_end = min(N_frames, base_idx + 2)
            ambient_baseline = np.mean(data[window_start:window_end], axis=0)  # (H, W)

            data_subtracted = data - ambient_baseline[np.newaxis, :, :]
            manifest.baseline_subtracted = True
            manifest.baseline_frame_index = base_idx
            manifest.baseline_mean_temperature_k = round(float(np.mean(ambient_baseline)), 3)
            manifest.applied_steps.append(
                f"Blind ambient baseline subtracted (Frame {base_idx}, mean T = {manifest.baseline_mean_temperature_k} K)."
            )
            data = data_subtracted

        # 4. Spatial Denoising Filter
        if smooth_sigma_px > 0.0:
            for k in range(N_frames):
                data[k] = gaussian_filter(data[k], sigma=smooth_sigma_px, mode="nearest")
            manifest.spatial_filter_applied = True
            manifest.applied_steps.append(f"Spatial Gaussian filter applied (sigma = {smooth_sigma_px} px).")

        manifest.final_shape = data.shape
        manifest.runtime_seconds = time.perf_counter() - start_t
        return data, t_vec, manifest
