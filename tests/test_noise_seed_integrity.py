"""
Stochastic Integrity and Deterministic Reproducibility Tests for Thermal Noise Injection.
"""

import hashlib
import numpy as np
import pytest

from lfmt.config import NoiseConfig, CameraConfig
from lfmt.noise import apply_noise_pipeline, add_thermal_camera_noise, measure_actual_snr_db, CameraNoisePreset


def compute_tensor_sha256(tensor: np.ndarray) -> str:
    """Compute SHA-256 hash of raw contiguous float64 array bytes."""
    return hashlib.sha256(np.ascontiguousarray(tensor, dtype=np.float64).tobytes()).hexdigest()


def test_seed_distinctness_across_10_seeds():
    """Verify that 10 distinct seeds produce 10 unique physical noise realizations."""
    clean_tensor = np.full((10, 32, 32), 295.0, dtype=np.float64)
    for k in range(10):
        clean_tensor[k] += np.sin(2 * np.pi * k / 10.0) * 1.5

    seeds = [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010]
    hashes = set()
    tensors = []

    for s in seeds:
        noise_cfg = NoiseConfig(preset="CONTROLLED_AWGN", snr_db=25.0, seed=s)
        cam_cfg = CameraConfig()
        noisy = apply_noise_pipeline(clean_tensor, noise_cfg, cam_cfg)
        h = compute_tensor_sha256(noisy)
        assert h not in hashes, f"Duplicate noise tensor detected for seed {s}!"
        hashes.add(h)
        tensors.append(noisy)

    assert len(hashes) == 10, "Expected 10 unique fingerprints for 10 distinct seeds"


def test_same_seed_exact_reproducibility():
    """Verify that running the same seed twice produces bit-for-bit identical tensors."""
    clean_tensor = np.full((10, 32, 32), 295.0, dtype=np.float64)
    noise_cfg_a = NoiseConfig(preset="CONTROLLED_AWGN", snr_db=30.0, seed=1007)
    noise_cfg_b = NoiseConfig(preset="CONTROLLED_AWGN", snr_db=30.0, seed=1007)
    cam_cfg = CameraConfig()

    noisy_a = apply_noise_pipeline(clean_tensor, noise_cfg_a, cam_cfg)
    noisy_b = apply_noise_pipeline(clean_tensor, noise_cfg_b, cam_cfg)

    assert np.array_equal(noisy_a, noisy_b), "Same seed failed bit-for-bit exact reproducibility!"
    assert compute_tensor_sha256(noisy_a) == compute_tensor_sha256(noisy_b)


def test_noise_config_seed_and_random_seed_alias():
    """Verify that NoiseConfig properly synchronizes seed and random_seed alias."""
    clean_tensor = np.full((10, 32, 32), 295.0, dtype=np.float64)
    cam_cfg = CameraConfig()

    cfg1 = NoiseConfig(snr_db=25.0, seed=1005)
    noisy1 = apply_noise_pipeline(clean_tensor, cfg1, cam_cfg)

    cfg2 = NoiseConfig(snr_db=25.0)
    cfg2.seed = 1005
    noisy2 = apply_noise_pipeline(clean_tensor, cfg2, cam_cfg)

    assert np.array_equal(noisy1, noisy2)
