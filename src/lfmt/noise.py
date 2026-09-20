"""
Noise Injection & Degradation Models for Infrared Thermography.

Supports:
- Additive White Gaussian Noise (AWGN) at specified SNR (30 dB, 25 dB, 20 dB)
- Spatially varying emissivity and surface roughness artifacts
- Non-uniform optical heating patterns (Gaussian roll-off)
- Fixed-pattern camera sensor noise and quantization
- Fully deterministic reproducible seeding
"""

from __future__ import annotations
import math
from typing import Optional, Tuple
import numpy as np

from lfmt.config import NoiseConfig


def add_awgn_noise(
    tensor: np.ndarray,
    snr_db: float | None,
    seed: int | None = 42
) -> np.ndarray:
    """
    Inject Additive White Gaussian Noise (AWGN) based on signal AC dynamic power.

    Args:
        tensor: Thermogram tensor of shape (n_frames, H, W).
        snr_db: Target Signal-to-Noise Ratio in decibels (e.g. 30, 25, 20). If None, returns copy.
        seed: Random seed for deterministic reproducibility.

    Returns:
        Noisy thermogram tensor with identical shape.
    """
    if snr_db is None:
        return tensor.copy()

    rng = np.random.default_rng(seed)
    # Calculate temporal AC signal variance across entire sequence
    # Subtract global baseline / mean to measure dynamic modulated signal power
    signal_ac = tensor - np.mean(tensor)
    signal_power = np.mean(signal_ac ** 2)

    if signal_power < 1e-12:
        return tensor.copy()

    # Noise power: SNR_dB = 10 * log10(P_signal / P_noise)
    # => P_noise = P_signal / 10^(SNR_dB / 10)
    noise_power = signal_power / (10.0 ** (snr_db / 10.0))
    noise_std = math.sqrt(noise_power)

    noise = rng.normal(loc=0.0, scale=noise_std, size=tensor.shape)
    return tensor + noise


def add_surface_emissivity_variation(
    tensor: np.ndarray,
    variation_fraction: float = 0.01,
    seed: int | None = 42
) -> np.ndarray:
    """
    Apply spatial surface emissivity non-uniformity (spatial multiplicative noise).
    """
    if variation_fraction <= 0.0:
        return tensor.copy()

    rng = np.random.default_rng(seed)
    H, W = tensor.shape[1], tensor.shape[2]
    # Spatial emissivity pattern centered at 1.0
    emissivity_map = 1.0 + rng.normal(0.0, variation_fraction, size=(1, H, W))
    return tensor * emissivity_map


def add_nonuniform_heating(
    tensor: np.ndarray,
    roll_off: float = 0.05
) -> np.ndarray:
    """
    Simulate non-uniform heating distribution (e.g., Gaussian center bias from flash/halogen lamps).
    """
    if roll_off <= 0.0:
        return tensor.copy()

    H, W = tensor.shape[1], tensor.shape[2]
    y = np.linspace(-1.0, 1.0, H)
    x = np.linspace(-1.0, 1.0, W)
    X, Y = np.meshgrid(x, y)
    R_sq = X**2 + Y**2
    # Center-biased heating field
    heating_profile = (1.0 - roll_off * R_sq)[np.newaxis, :, :]

    # Modulate thermal rise above ambient
    T_min = np.min(tensor)
    T_rise = tensor - T_min
    return T_min + T_rise * heating_profile


def apply_noise_pipeline(
    tensor: np.ndarray,
    config: NoiseConfig
) -> np.ndarray:
    """
    Execute full configured noise degradation pipeline.
    """
    noisy = tensor.copy()

    if config.emissivity_variation > 0:
        noisy = add_surface_emissivity_variation(
            noisy,
            variation_fraction=config.emissivity_variation,
            seed=config.seed
        )

    if config.spatial_nonuniformity > 0:
        noisy = add_nonuniform_heating(
            noisy,
            roll_off=config.spatial_nonuniformity
        )

    if config.snr_db is not None:
        noisy = add_awgn_noise(
            noisy,
            snr_db=config.snr_db,
            seed=config.seed
        )

    return noisy
