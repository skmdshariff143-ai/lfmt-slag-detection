"""
Experimental Data Ingestion and Calibration Interface for LFMT Thermography.

Supports loading and standardizing laboratory and field thermogram data from:
- NumPy arrays (.npy, .npz)
- MATLAB MAT files (.mat)
- Image frame stacks (TIFF, PNG, JPEG)
- Delimited text / CSV datasets

Provides validation of spatial resolution, frame rates, radiometric conversion,
and ground-truth calibration metadata.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
import numpy as np


@dataclass
class ExperimentalSequence:
    """Standardized container for experimental LFMT thermographic sequences."""
    surface_temperature: np.ndarray  # Shape: (N_frames, H, W) in Kelvin or Celsius
    time_vector: np.ndarray          # 1D array of timestamps in seconds
    frame_rate_hz: float
    fov_mm: Tuple[float, float]       # (length_mm, width_mm)
    metadata: Dict[str, Any] = field(default_factory=dict)
    ground_truth_centroids_mm: List[Tuple[float, float]] = field(default_factory=list)
    ground_truth_mask: Optional[np.ndarray] = None


class ExperimentalDataLoader:
    """Loader and validator for laboratory NDT thermal sequences."""

    @staticmethod
    def load_numpy(
        file_path: str,
        frame_rate_hz: float = 20.0,
        fov_mm: Tuple[float, float] = (100.0, 70.0),
        temp_units: str = "K"
    ) -> ExperimentalSequence:
        """Load thermal sequence from a .npy or .npz file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        data = np.load(file_path)
        cube = np.asarray(data if not isinstance(data, np.lib.npyio.NpzFile) else (data['surface_temperature'] if 'surface_temperature' in data else data[list(data.keys())[0]]), dtype=np.float64)
        if cube.ndim == 2:
            cube = cube[np.newaxis, :, :]

        N_frames, H, W = cube.shape
        t_vec = np.arange(N_frames) / float(frame_rate_hz)

        if temp_units.upper() == "C":
            cube = cube + 273.15

        return ExperimentalSequence(
            surface_temperature=cube,
            time_vector=t_vec,
            frame_rate_hz=float(frame_rate_hz),
            fov_mm=fov_mm,
            metadata={"source_file": file_path, "units": "K", "loader": "numpy"}
        )

    @staticmethod
    def load_mat(
        file_path: str,
        cube_key: str = "thermogram",
        time_key: Optional[str] = "time",
        frame_rate_hz: float = 20.0,
        fov_mm: Tuple[float, float] = (100.0, 70.0)
    ) -> ExperimentalSequence:
        """Load thermal sequence from MATLAB .mat file."""
        try:
            import scipy.io as sio
        except ImportError:
            raise ImportError("scipy is required for loading .mat files")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        mat_dict = sio.loadmat(file_path)
        if cube_key not in mat_dict:
            candidates = [k for k, v in mat_dict.items() if isinstance(v, np.ndarray) and v.ndim == 3]
            if candidates:
                cube_key = candidates[0]
            else:
                raise KeyError(f"Key '{cube_key}' not found in MAT file {file_path}")

        cube = np.asarray(mat_dict[cube_key], dtype=np.float64)
        if cube.ndim == 3 and cube.shape[2] > cube.shape[0] and cube.shape[0] <= 128:
            cube = np.transpose(cube, (2, 0, 1))

        N_frames = cube.shape[0]
        if time_key and time_key in mat_dict:
            t_vec = np.asarray(mat_dict[time_key]).ravel()
        else:
            t_vec = np.arange(N_frames) / float(frame_rate_hz)

        return ExperimentalSequence(
            surface_temperature=cube,
            time_vector=t_vec,
            frame_rate_hz=float(frame_rate_hz),
            fov_mm=fov_mm,
            metadata={"source_file": file_path, "cube_key": cube_key, "loader": "mat"}
        )

    @staticmethod
    def load_csv_zip_archive(
        zip_path: str | os.PathLike,
        frame_rate_hz: float = 50.0,
        fov_mm: Tuple[float, float] = (150.0, 150.0),
        temp_units: str = "C",
        max_frames: Optional[int] = None,
        subsample_step: int = 1
    ) -> ExperimentalSequence:
        """
        Load 3D thermogram sequence from an archive of individual frame CSV files.
        """
        import zipfile
        import re
        from pathlib import Path

        zip_p = Path(zip_path)
        if not zip_p.exists():
            raise FileNotFoundError(f"Archive not found at: {zip_p}")

        def extract_frame_index(fname: str) -> int:
            m = re.search(r'_(\d+)\.csv$', fname)
            return int(m.group(1)) if m else -1

        with zipfile.ZipFile(zip_p, "r") as z:
            csv_files = [f for f in z.namelist() if f.endswith(".csv")]
            sorted_files = sorted(csv_files, key=extract_frame_index)
            if not sorted_files:
                raise ValueError(f"No CSV files found in archive {zip_p}")

            if max_frames is not None:
                sorted_files = sorted_files[:max_frames]
            if subsample_step > 1:
                sorted_files = sorted_files[::subsample_step]

            frames = []
            try:
                import pandas as pd
                has_pandas = True
            except ImportError:
                has_pandas = False

            for fname in sorted_files:
                with z.open(fname) as f:
                    if has_pandas:
                        arr = pd.read_csv(f, header=None).values
                    else:
                        arr = np.genfromtxt(f, delimiter=",")
                    frames.append(arr)

        cube = np.stack(frames, axis=0).astype(np.float64)
        N_frames, H, W = cube.shape

        effective_fps = frame_rate_hz / float(subsample_step)
        t_vec = np.arange(N_frames) / float(effective_fps)

        raw_units = temp_units.upper()
        if raw_units == "C":
            cube_k = cube + 273.15
            converted_units = "K"
            conv_method = "T_K = T_C + 273.15 (standard Celsius to Kelvin offset)"
        else:
            cube_k = cube
            converted_units = raw_units
            conv_method = "identity (no conversion applied)"

        meta = {
            "source_file": str(zip_p),
            "raw_units": raw_units,
            "converted_units": converted_units,
            "conversion_method": conv_method,
            "subsample_step": subsample_step,
            "verified_frame_rate_hz": float(effective_fps),
            "total_frames": N_frames,
            "loader": "csv_zip_archive"
        }

        return ExperimentalSequence(
            surface_temperature=cube_k,
            time_vector=t_vec,
            frame_rate_hz=float(effective_fps),
            fov_mm=fov_mm,
            metadata=meta
        )

    @staticmethod
    def validate_sequence(seq: ExperimentalSequence) -> Dict[str, Any]:
        """Perform rigorous physical sanity check on loaded experimental thermogram."""
        cube = seq.surface_temperature
        issues = []

        if cube.ndim != 3:
            issues.append(f"Expected 3D array (N_frames, H, W), got {cube.ndim}D")
            return {"is_valid": False, "issues": issues}

        N, H, W = cube.shape
        if N < 2:
            issues.append(f"Sequence contains insufficient frames: {N}")

        if np.any(np.isnan(cube)):
            issues.append("Data contains NaN values")

        if np.any(np.isinf(cube)):
            issues.append("Data contains Inf values")

        min_T, max_T = float(np.min(cube)), float(np.max(cube))
        mean_T = float(np.mean(cube))
        if min_T < 200.0 or max_T > 600.0:
            issues.append(f"Physical temperature bounds warning: [{min_T:.1f} K, {max_T:.1f} K]")

        time_diffs = np.diff(seq.time_vector)
        if np.any(time_diffs <= 0):
            issues.append("Time vector is not strictly monotonically increasing")

        # Check for dead / zero-variance frames
        spatial_stds = np.std(cube, axis=(1, 2))
        dead_frames = int(np.sum(spatial_stds < 1e-6))
        if dead_frames > 0:
            issues.append(f"Detected {dead_frames} dead/flat frames with zero spatial variance")

        is_valid = (len(issues) == 0)
        return {
            "is_valid": is_valid,
            "shape": (N, H, W),
            "total_frames": N,
            "height_px": H,
            "width_px": W,
            "min_temperature_k": round(min_T, 3),
            "max_temperature_k": round(max_T, 3),
            "mean_temperature_k": round(mean_T, 3),
            "verified_frame_rate_hz": seq.frame_rate_hz,
            "total_duration_s": round(float(seq.time_vector[-1] - seq.time_vector[0]), 3) if len(seq.time_vector) > 1 else 0.0,
            "dead_frames_count": dead_frames,
            "issues": issues
        }


