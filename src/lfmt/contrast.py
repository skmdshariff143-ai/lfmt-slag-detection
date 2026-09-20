r"""
Raw Thermal Contrast Analysis Module for Infrared Thermography.

Computes absolute and normalized differential thermal contrast curves:
    \Delta T(t) = T_{defect}(t) - T_{sound}(t)
    C(t) = \frac{T_{defect}(t) - T_{sound}(t)}{|T_{sound}(t)| + \epsilon}
and extracts peak contrast time t_max and optimal contrast spatial maps.
"""

from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
import numpy as np


@dataclass
class RawContrastResult:
    """
    Raw Thermal Contrast Output.

    Attributes:
        contrast_map: 2D array (H, W) of differential thermal contrast at peak contrast time.
        time_vector: 1D time array [s].
        t_defect_curve: 1D temporal profile of defect center [K].
        t_sound_curve: 1D temporal profile of sound background [K].
        delta_t_curve: 1D absolute temperature difference curve Delta T(t) [K].
        normalized_contrast_curve: 1D normalized contrast curve C(t) [-].
        max_contrast_val: Maximum peak differential temperature [K].
        t_max_contrast_s: Time of maximum contrast occurrence [s].
        frame_max_contrast: Frame index where maximum contrast occurs.
        runtime_seconds: Execution time in seconds.
    """
    contrast_map: np.ndarray
    time_vector: np.ndarray
    t_defect_curve: np.ndarray
    t_sound_curve: np.ndarray
    delta_t_curve: np.ndarray
    normalized_contrast_curve: np.ndarray
    max_contrast_val: float
    t_max_contrast_s: float
    frame_max_contrast: int
    runtime_seconds: float
    metadata: Dict[str, Any]


class RawThermalContrast:
    """
    Thermal Contrast Evaluator.
    """

    def __init__(self, mode: str = "blind"):
        self.mode = mode.lower().strip()

    def process(
        self,
        thermograms: np.ndarray,
        time_vector: np.ndarray,
        ground_truth_mask: Optional[np.ndarray] = None
    ) -> RawContrastResult:
        """
        Compute temporal contrast metrics and peak contrast image.

        Args:
            thermograms: 3D array (n_frames, H, W).
            time_vector: 1D time array (n_frames,).
            ground_truth_mask: Optional 2D boolean mask. ONLY used if mode == 'oracle'.

        Returns:
            RawContrastResult instance.
        """
        start_t = time.perf_counter()
        n_frames, H, W = thermograms.shape

        if self.mode == "oracle" and ground_truth_mask is not None and np.any(ground_truth_mask) and np.any(~ground_truth_mask):
            defect_mask = ground_truth_mask
            sound_mask = ~defect_mask
            t_defect = np.mean(thermograms[:, defect_mask], axis=1)  # (n_frames,)
            t_sound = np.mean(thermograms[:, sound_mask], axis=1)    # (n_frames,)
            delta_t = t_defect - t_sound
            peak_idx = int(np.argmax(np.abs(delta_t)))
            max_contrast = float(np.abs(delta_t[peak_idx]))
            t_peak = float(time_vector[peak_idx])
            sound_baseline_at_peak = float(np.mean(thermograms[peak_idx, sound_mask]))
            contrast_map = thermograms[peak_idx] - sound_baseline_at_peak
        else:
            # Blind mode: purely data-driven without spatial assumptions
            # Find frame with maximum spatial standard deviation / non-uniformity
            spatial_stds = np.std(thermograms, axis=(1, 2))
            peak_idx = int(np.argmax(spatial_stds))
            t_peak = float(time_vector[peak_idx])
            
            # Baseline is spatial median of peak frame
            frame_peak = thermograms[peak_idx]
            sound_baseline_at_peak = float(np.median(frame_peak))
            contrast_map = frame_peak - sound_baseline_at_peak
            
            # Global mean temperature temporal curves
            t_sound = np.mean(thermograms, axis=(1, 2))
            t_defect = np.max(thermograms, axis=(1, 2))
            delta_t = t_defect - t_sound
            max_contrast = float(np.max(spatial_stds))

        eps = 1e-6
        norm_contrast = delta_t / (np.abs(t_sound) + eps)

        elapsed = time.perf_counter() - start_t

        metadata = {
            "mode": self.mode,
            "peak_frame": peak_idx,
            "peak_time_s": t_peak,
            "max_delta_T_k": max_contrast,
            "runtime_s": elapsed,
        }

        return RawContrastResult(
            contrast_map=contrast_map,
            time_vector=time_vector,
            t_defect_curve=t_defect,
            t_sound_curve=t_sound,
            delta_t_curve=delta_t,
            normalized_contrast_curve=norm_contrast,
            max_contrast_val=max_contrast,
            t_max_contrast_s=t_peak,
            frame_max_contrast=peak_idx,
            runtime_seconds=elapsed,
            metadata=metadata
        )
