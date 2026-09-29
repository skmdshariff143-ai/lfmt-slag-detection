"""
Matched Filtering & Pulse Compression Module for LFMT.

Performs vectorised FFT-based cross-correlation between pixel thermal transients
and the modulated chirp excitation reference waveform to compress thermal energy
and extract defect impedance and time-of-flight maps.
"""

from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Dict, Any
import numpy as np
from scipy.signal import fftconvolve

from lfmt.excitation import LFMTExcitation


@dataclass
class PulseCompressionResult:
    """
    Output container for LFMT matched filter / pulse compression.

    Attributes:
        peak_correlation_map: 2D array (H, W) of maximum cross-correlation peak amplitude.
        delay_map_s: 2D array (H, W) of time delay (in seconds) where correlation peak occurs.
        normalized_map: 2D array (H, W) normalized to [0, 1].
        correlation_tensor: Full 3D cross-correlation sequence (n_tau, H, W).
        time_lags_s: 1D array of correlation time lags [s].
        runtime_seconds: Elapsed processing time in seconds.
        metadata: Processing parameters and metadata.
    """
    peak_correlation_map: np.ndarray
    delay_map_s: np.ndarray
    normalized_map: np.ndarray
    correlation_tensor: np.ndarray
    time_lags_s: np.ndarray
    runtime_seconds: float
    metadata: Dict[str, Any]


class LFMTMatchedFilter:
    """
    Vectorized Pulse Compression Matched Filter.
    """

    def __init__(self, excitation: LFMTExcitation, zero_mean_reference: bool = True):
        self.excitation = excitation
        self.zero_mean_reference = zero_mean_reference

    def process(self, thermograms: np.ndarray, time_vector: np.ndarray) -> PulseCompressionResult:
        """
        Execute pixel-wise matched filtering across thermogram tensor.

        Args:
            thermograms: 3D array of shape (n_frames, H, W).
            time_vector: 1D array of shape (n_frames,) in seconds.

        Returns:
            PulseCompressionResult object.
        """
        start_t = time.perf_counter()
        n_frames, H, W = thermograms.shape
        dt = float(time_vector[1] - time_vector[0]) if len(time_vector) > 1 else 1.0 / self.excitation.sampling_rate_hz

        # 1. Generate reference waveform
        ref_signal = self.excitation.reference_signal(time_vector, zero_mean=self.zero_mean_reference)

        # 2. Reshape thermograms to 2D (time, pixels)
        T_2d = thermograms.reshape(n_frames, H * W)

        # Remove DC/mean component from each pixel signal
        T_ac = T_2d - np.mean(T_2d, axis=0, keepdims=True)

        # 3. Vectorized FFT correlation: correlate(T_ac, ref)
        # Flip reference for convolution-based correlation: correlate(x, y) = convolve(x, y[::-1])
        ref_flipped = ref_signal[::-1, np.newaxis]

        # Use scipy.signal.fftconvolve along axis 0
        corr_2d = fftconvolve(T_ac, ref_flipped, mode="same", axes=0)
        corr_tensor = corr_2d.reshape(n_frames, H, W)

        # Time lags
        lags = (np.arange(n_frames) - n_frames // 2) * dt

        # 4. Extract peak correlation and peak delay map
        # Find absolute peak across time axis
        peak_idx = np.argmax(np.abs(corr_2d), axis=0)  # shape: (H*W,)
        
        # Peak values
        peak_vals = np.abs(np.take_along_axis(corr_2d, peak_idx[np.newaxis, :], axis=0).squeeze(0))
        peak_map = peak_vals.reshape(H, W)

        # Time delay at peak
        delay_map = (lags[peak_idx]).reshape(H, W)

        # Normalized map [0, 1]
        p_min, p_max = np.min(peak_map), np.max(peak_map)
        denom = p_max - p_min if (p_max - p_min) > 1e-12 else 1.0
        norm_map = (peak_map - p_min) / denom

        elapsed = time.perf_counter() - start_t

        metadata = {
            "method": "FFT Matched Filter",
            "zero_mean_reference": self.zero_mean_reference,
            "dt_s": dt,
            "tensor_shape": list(thermograms.shape),
            "runtime_s": elapsed,
        }

        return PulseCompressionResult(
            peak_correlation_map=peak_map,
            delay_map_s=delay_map,
            normalized_map=norm_map,
            correlation_tensor=corr_tensor,
            time_lags_s=lags,
            runtime_seconds=elapsed,
            metadata=metadata
        )
