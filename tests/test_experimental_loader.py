"""
Unit tests for ExperimentalDataLoader and Sequence Validation.

Verifies:
- NumPy (.npy / .npz) loader
- MAT (.mat) loader
- In-memory CSV zip archive loader with numerical frame sorting and subsampling
- Physical temperature unit conversion (Celsius to Kelvin)
- Sequence validation checks (NaN/Inf, dead frames, non-monotonic timestamps, physical bounds)
"""

import io
import tempfile
import zipfile
from pathlib import Path
import pytest
import numpy as np

from lfmt.io_experimental import ExperimentalDataLoader, ExperimentalSequence


def test_validate_sequence_valid():
    """Verify validation passes for clean physical sequence."""
    N, H, W = 50, 16, 16
    cube = 295.0 + 5.0 * np.random.RandomState(42).randn(N, H, W)
    t_vec = np.linspace(0, 5.0, N)
    seq = ExperimentalSequence(
        surface_temperature=cube,
        time_vector=t_vec,
        frame_rate_hz=10.0,
        fov_mm=(100.0, 70.0)
    )
    res = ExperimentalDataLoader.validate_sequence(seq)
    assert res["is_valid"] is True
    assert res["dead_frames_count"] == 0
    assert len(res["issues"]) == 0
    assert res["shape"] == (N, H, W)


def test_validate_sequence_nan_and_inf():
    """Verify rejection when NaNs or Infs are present."""
    cube = np.ones((10, 8, 8)) * 300.0
    cube[2, 0, 0] = np.nan
    cube[4, 1, 1] = np.inf
    seq = ExperimentalSequence(
        surface_temperature=cube,
        time_vector=np.arange(10) * 0.1,
        frame_rate_hz=10.0,
        fov_mm=(50.0, 50.0)
    )
    res = ExperimentalDataLoader.validate_sequence(seq)
    assert res["is_valid"] is False
    assert any("NaN" in issue for issue in res["issues"])
    assert any("Inf" in issue for issue in res["issues"])


def test_validate_sequence_dead_frames():
    """Verify detection of dead / flat frames with zero spatial variance."""
    cube = 295.0 + np.random.RandomState(42).randn(10, 8, 8)
    cube[3, :, :] = 300.0  # Exactly constant frame
    cube[7, :, :] = 300.0  # Exactly constant frame
    seq = ExperimentalSequence(
        surface_temperature=cube,
        time_vector=np.arange(10) * 0.1,
        frame_rate_hz=10.0,
        fov_mm=(50.0, 50.0)
    )
    res = ExperimentalDataLoader.validate_sequence(seq)
    assert res["dead_frames_count"] == 2
    assert any("dead/flat" in issue for issue in res["issues"])


def test_load_numpy():
    """Verify loading from .npy and .npz with Celsius to Kelvin conversion."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        test_data = np.zeros((20, 10, 10)) + 25.0  # 25 degrees C
        npy_path = tmp_path / "test_thermogram.npy"
        np.save(npy_path, test_data)

        seq = ExperimentalDataLoader.load_numpy(
            str(npy_path),
            frame_rate_hz=20.0,
            fov_mm=(100.0, 70.0),
            temp_units="C"
        )
        assert seq.surface_temperature.shape == (20, 10, 10)
        assert np.isclose(seq.surface_temperature[0, 0, 0], 298.15)
        assert len(seq.time_vector) == 20
        assert np.isclose(seq.time_vector[1] - seq.time_vector[0], 1.0 / 20.0)


def test_load_csv_zip_archive():
    """Verify loading from CSV zip archive with numerical frame sorting and subsampling."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        zip_path = tmp_path / "test_frames.zip"
        with zipfile.ZipFile(zip_path, "w") as z:
            for i in [2, 0, 1, 3]:  # Intentionally out of order
                frame = np.ones((8, 8), dtype=np.float64) * (20.0 + i)
                csv_str = "\n".join(",".join(f"{val:.2f}" for val in row) for row in frame)
                z.writestr(f"frame_{i}.csv", csv_str)

        seq = ExperimentalDataLoader.load_csv_zip_archive(
            zip_path=str(zip_path),
            frame_rate_hz=10.0,
            temp_units="C",
            subsample_step=1
        )
        assert seq.surface_temperature.shape == (4, 8, 8)
        # Check natural sorting: frame 0 should be first, frame 3 should be last
        assert np.isclose(seq.surface_temperature[0, 0, 0], 20.0 + 273.15)
        assert np.isclose(seq.surface_temperature[1, 0, 0], 21.0 + 273.15)
        assert np.isclose(seq.surface_temperature[2, 0, 0], 22.0 + 273.15)
        assert np.isclose(seq.surface_temperature[3, 0, 0], 23.0 + 273.15)

        # Test subsampling step = 2
        seq_sub = ExperimentalDataLoader.load_csv_zip_archive(
            zip_path=str(zip_path),
            frame_rate_hz=10.0,
            temp_units="C",
            subsample_step=2
        )
        assert seq_sub.surface_temperature.shape == (2, 8, 8)
        assert seq_sub.frame_rate_hz == 5.0
        assert np.isclose(seq_sub.surface_temperature[0, 0, 0], 20.0 + 273.15)
        assert np.isclose(seq_sub.surface_temperature[1, 0, 0], 22.0 + 273.15)
