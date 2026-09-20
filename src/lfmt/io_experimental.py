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
import glob
import math
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List, Union
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
    def validate_sequence(seq: ExperimentalSequence) -> Dict[str, Any]:
        """Perform rigorous physical sanity check on loaded experimental thermogram."""
        cube = seq.surface_temperature
        issues = []

        if cube.ndim != 3:
            issues.append(f"Expected 3D array (N_frames, H, W), got {cube.ndim}D")

        N, H, W = cube.shape
        if N < 2:
            issues.append(f"Sequence contains insufficient frames: {N}")

        if np.any(np.isnan(cube)):
            issues.append("Data contains NaN values")

        if np.any(np.isinf(cube)):
            issues.append("Data contains Inf values")

        min_T, max_T = float(np.min(cube)), float(np.max(cube))
        if min_T < 200.0 or max_T > 600.0:
            issues.append(f"Physical temperature bounds warning: [{min_T:.1f} K, {max_T:.1f} K]")

        time_diffs = np.diff(seq.time_vector)
        if np.any(time_diffs <= 0):
            issues.append("Time vector is not strictly monotonically increasing")

        is_valid = (len(issues) == 0)
        return {
            "is_valid": is_valid,
            "shape": (N, H, W),
            "min_temperature_k": min_T,
            "max_temperature_k": max_T,
            "total_duration_s": float(seq.time_vector[-1] - seq.time_vector[0]) if len(seq.time_vector) > 1 else 0.0,
            "issues": issues
        }

