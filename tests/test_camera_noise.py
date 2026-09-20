"""Unit tests for Virtual IR Camera and Noise modules."""

import pytest
import numpy as np
import tempfile
from pathlib import Path
from lfmt.config import load_config, CameraConfig, NoiseConfig
from lfmt.simulation.finite_difference import FiniteDifferenceBackend
from lfmt.camera import VirtualIRCamera, VirtualCameraCapture
from lfmt.noise import add_awgn_noise, apply_noise_pipeline


def test_camera_capture_and_serialization():
    config = load_config("configs/quick.yaml")
    config.simulation.spatial_resolution = {"nx": 20, "ny": 16, "nz": 10}
    config.simulation.total_time_s = 1.0
    config.simulation.timestep_s = 0.2

    sim = FiniteDifferenceBackend().run(config)

    cam_cfg = CameraConfig(resolution_x=32, resolution_y=32, sampling_rate_hz=5.0)
    camera = VirtualIRCamera(cam_cfg)
    capture = camera.capture(sim)

    assert capture.thermograms.shape == (6, 32, 32)
    assert capture.ground_truth_mask.shape == (32, 32)
    assert np.any(capture.ground_truth_mask)  # Defect mask should have positive pixels

    # Test saving and loading
    with tempfile.TemporaryDirectory() as tmpdir:
        case_dir = capture.save_case(tmpdir, case_id="test_case_01")
        assert (case_dir / "thermograms.npz").exists()
        assert (case_dir / "metadata.json").exists()
        assert (case_dir / "ground_truth_mask.npy").exists()

        loaded = VirtualCameraCapture.load_case(case_dir)
        assert loaded.thermograms.shape == capture.thermograms.shape
        assert np.array_equal(loaded.ground_truth_mask, capture.ground_truth_mask)


def test_noise_awgn_snr():
    # Synthetic signal
    t = np.linspace(0, 10, 100)
    signal = np.sin(2 * np.pi * 0.5 * t)[:, np.newaxis, np.newaxis]
    tensor = np.broadcast_to(signal, (100, 20, 20)).copy()

    noisy_30 = add_awgn_noise(tensor, snr_db=30, seed=42)
    noisy_20 = add_awgn_noise(tensor, snr_db=20, seed=42)

    noise_30_var = np.var(noisy_30 - tensor)
    noise_20_var = np.var(noisy_20 - tensor)

    # 20 dB noise should have higher power/variance than 30 dB noise
    assert noise_20_var > noise_30_var * 5.0

    # Test reproducible seeding
    noisy_20_repeat = add_awgn_noise(tensor, snr_db=20, seed=42)
    assert np.allclose(noisy_20, noisy_20_repeat)
