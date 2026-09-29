"""
Universal Thermographic Input Analyzer & Physical Inspector.

Inspects arbitrary input files, directories, image stacks, and numerical cubes to detect:
- Input format and structure (Single frame, 3D sequence, CSV archive, MAT, NPY, TIFF, Simulation)
- Physical data representation (Radiometric temperature, Radiance, Raw counts, Intensity, Visual RGB)
- Data integrity (NaNs, Infs, dead/flat frames, timestamp monotonicity)
- Calibration status (Temperature units, Frame rate, FOV, Pixel pitch, Excitation metadata)
- Quality status and physical warnings
"""

from __future__ import annotations
import json
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List, Union
import numpy as np


class InputType(str, Enum):
    THERMAL_SINGLE_IMAGE = "THERMAL_SINGLE_IMAGE"
    THERMAL_SEQUENCE = "THERMAL_SEQUENCE"
    LFMT_SEQUENCE = "LFMT_SEQUENCE"
    PULSED_SEQUENCE = "PULSED_SEQUENCE"
    LOCK_IN_SEQUENCE = "LOCK_IN_SEQUENCE"
    SIMULATION_SEQUENCE = "SIMULATION_SEQUENCE"
    VISIBLE_IMAGE = "VISIBLE_IMAGE"
    UNKNOWN_IMAGE = "UNKNOWN_IMAGE"
    THERMAL_VIDEO = "THERMAL_VIDEO"
    CSV_SEQUENCE = "CSV_SEQUENCE"
    MAT_SEQUENCE = "MAT_SEQUENCE"
    NUMPY_SEQUENCE = "NUMPY_SEQUENCE"


class DataRepresentation(str, Enum):
    RADIOMETRIC_TEMPERATURE = "RADIOMETRIC_TEMPERATURE"
    RADIANCE = "RADIANCE"
    RAW_SENSOR_COUNTS = "RAW_SENSOR_COUNTS"
    NORMALIZED_INTENSITY = "NORMALIZED_INTENSITY"
    VISIBLE_RGB = "VISIBLE_RGB"
    UNKNOWN = "UNKNOWN"


class QualityStatus(str, Enum):
    VALID = "VALID"
    VALID_WITH_WARNINGS = "VALID_WITH_WARNINGS"
    INSUFFICIENT_METADATA = "INSUFFICIENT_METADATA"
    UNSUPPORTED = "UNSUPPORTED"
    CORRUPT = "CORRUPT"


@dataclass
class InputInspectionResult:
    """Comprehensive inspection report for arbitrary thermographic input."""
    input_type: InputType
    data_representation: DataRepresentation
    quality_status: QualityStatus
    shape: Tuple[int, ...]
    n_frames: int
    height: int
    width: int
    channels: int
    dtype: str
    min_val: float
    max_val: float
    mean_val: float
    std_val: float
    nan_count: int
    inf_count: int
    dead_frames_count: int
    is_time_monotonic: bool
    frame_rate_hz: Optional[float]
    duration_s: Optional[float]
    temperature_units: str  # "K", "C", "RAW_COUNTS", "NORMALIZED", "UNKNOWN"
    is_radiometric: bool
    timestamps_available: bool
    excitation_type: str    # "lfmt", "pulsed", "lock_in", "unknown"
    excitation_metadata: Dict[str, Any] = field(default_factory=dict)
    fov_mm: Optional[Tuple[float, float]] = None
    pixel_pitch_mm: Optional[float] = None
    warnings: List[str] = field(default_factory=list)
    raw_metadata: Dict[str, Any] = field(default_factory=dict)
    loaded_cube_k: Optional[np.ndarray] = None
    time_vector: Optional[np.ndarray] = None


class UniversalInputAnalyzer:
    """Universal loader, format detector, and physical inspector."""

    @staticmethod
    def inspect(
        source: Union[str, Path, np.ndarray, Dict[str, Any]],
        metadata_override: Optional[Dict[str, Any]] = None
    ) -> InputInspectionResult:
        """Inspect and parse an arbitrary source into a standardized InputInspectionResult."""
        meta_override = metadata_override or {}
        warnings: List[str] = []

        # Case 1: Direct in-memory NumPy array
        if isinstance(source, np.ndarray):
            return UniversalInputAnalyzer._inspect_numpy_array(
                source, meta_override, warnings, source_name="in_memory_array"
            )

        source_path = Path(source)
        if not source_path.exists():
            return InputInspectionResult(
                input_type=InputType.UNKNOWN_IMAGE,
                data_representation=DataRepresentation.UNKNOWN,
                quality_status=QualityStatus.CORRUPT,
                shape=(0,),
                n_frames=0,
                height=0,
                width=0,
                channels=0,
                dtype="unknown",
                min_val=0.0,
                max_val=0.0,
                mean_val=0.0,
                std_val=0.0,
                nan_count=0,
                inf_count=0,
                dead_frames_count=0,
                is_time_monotonic=False,
                frame_rate_hz=None,
                duration_s=None,
                temperature_units="UNKNOWN",
                is_radiometric=False,
                timestamps_available=False,
                excitation_type="unknown",
                warnings=[f"Source path does not exist: {source_path}"]
            )

        # Case 2: Directory (Simulation case or multi-file stack)
        if source_path.is_dir():
            return UniversalInputAnalyzer._inspect_directory(source_path, meta_override, warnings)

        # Case 3: Archive (ZIP of CSV frames or NPZ)
        suffix = source_path.suffix.lower()
        if suffix == ".zip":
            return UniversalInputAnalyzer._inspect_zip_archive(source_path, meta_override, warnings)
        elif suffix in (".npy", ".npz"):
            return UniversalInputAnalyzer._inspect_numpy_file(source_path, meta_override, warnings)
        elif suffix == ".mat":
            return UniversalInputAnalyzer._inspect_mat_file(source_path, meta_override, warnings)
        elif suffix in (".csv", ".txt", ".dat"):
            return UniversalInputAnalyzer._inspect_single_csv(source_path, meta_override, warnings)
        elif suffix in (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"):
            return UniversalInputAnalyzer._inspect_image_file(source_path, meta_override, warnings)
        else:
            warnings.append(f"Unrecognized file extension '{suffix}', attempting generic array parsing.")
            return UniversalInputAnalyzer._inspect_image_file(source_path, meta_override, warnings)

    @staticmethod
    def _inspect_numpy_array(
        arr: np.ndarray,
        meta: Dict[str, Any],
        warnings: List[str],
        source_name: str = "array"
    ) -> InputInspectionResult:
        shape = arr.shape
        nan_count = int(np.isnan(arr).sum())
        inf_count = int(np.isinf(arr).sum())
        
        clean_arr = np.nan_to_num(arr, nan=293.15, posinf=600.0, neginf=0.0)
        min_v, max_v = float(np.min(clean_arr)), float(np.max(clean_arr))
        mean_v, std_v = float(np.mean(clean_arr)), float(np.std(clean_arr))

        # Detect dimensions & representation
        if arr.ndim == 2:
            n_frames, H, W, channels = 1, shape[0], shape[1], 1
            input_type = InputType.THERMAL_SINGLE_IMAGE
            cube = clean_arr[np.newaxis, :, :]
            dead_frames = 0
        elif arr.ndim == 3:
            if shape[2] in (3, 4) and shape[0] > 10 and shape[1] > 10:
                # Likely H x W x RGB visible image
                n_frames, H, W, channels = 1, shape[0], shape[1], shape[2]
                input_type = InputType.VISIBLE_IMAGE
                cube = np.mean(clean_arr[:, :, :3], axis=2)[np.newaxis, :, :]
                dead_frames = 0
                warnings.append("Input is a 3-channel visual/RGB photograph. Radiometric temperature cannot be inferred.")
            else:
                n_frames, H, W, channels = shape[0], shape[1], shape[2], 1
                input_type = InputType.THERMAL_SEQUENCE
                cube = clean_arr
                spatial_stds = np.std(cube, axis=(1, 2))
                dead_frames = int(np.sum(spatial_stds < 1e-6))
        elif arr.ndim == 4:
            # (N, H, W, C)
            n_frames, H, W, channels = shape[0], shape[1], shape[2], shape[3]
            input_type = InputType.THERMAL_SEQUENCE
            cube = np.mean(clean_arr, axis=3)
            dead_frames = int(np.sum(np.std(cube, axis=(1, 2)) < 1e-6))
        else:
            warnings.append(f"Unsupported array rank {arr.ndim}")
            n_frames, H, W, channels = 1, shape[0] if len(shape) > 0 else 0, shape[1] if len(shape) > 1 else 0, 1
            input_type = InputType.UNKNOWN_IMAGE
            cube = np.zeros((1, max(1, H), max(1, W)))
            dead_frames = 0

        # Physical representation & units inference
        rep, units, is_radiometric, exc_type, fps, fov = UniversalInputAnalyzer._infer_representation(
            min_v, max_v, input_type, meta, warnings
        )

        # Convert to Kelvin if Celsius
        if units == "C":
            cube_k = cube + 273.15
            temp_units = "K"
        elif units == "K":
            cube_k = cube
            temp_units = "K"
        else:
            cube_k = cube
            temp_units = units

        # Frame rate & timestamps
        t_vec = meta.get("time_vector")
        if t_vec is not None and len(t_vec) == n_frames:
            t_vec = np.asarray(t_vec, dtype=float)
            is_monotonic = bool(np.all(np.diff(t_vec) > 0)) if len(t_vec) > 1 else True
            dur_s = float(t_vec[-1] - t_vec[0]) if len(t_vec) > 1 else 0.0
            timestamps_avail = True
        else:
            effective_fps = float(fps or 10.0)
            t_vec = np.arange(n_frames) / effective_fps
            is_monotonic = True
            dur_s = float(t_vec[-1] - t_vec[0]) if len(t_vec) > 1 else 0.0
            timestamps_avail = (n_frames > 1 and fps is not None)

        # Check LFMT excitation metadata
        exc_meta = meta.get("excitation", {})
        if exc_meta.get("type", "").lower() == "lfmt" or "f0_hz" in exc_meta or "f0" in meta:
            input_type = InputType.LFMT_SEQUENCE
            exc_type = "lfmt"

        # Quality status
        if nan_count > 0 or inf_count > 0 or dead_frames > 0:
            quality = QualityStatus.VALID_WITH_WARNINGS
        elif rep == DataRepresentation.UNKNOWN or units == "UNKNOWN":
            quality = QualityStatus.INSUFFICIENT_METADATA
        else:
            quality = QualityStatus.VALID

        return InputInspectionResult(
            input_type=input_type,
            data_representation=rep,
            quality_status=quality,
            shape=shape,
            n_frames=n_frames,
            height=H,
            width=W,
            channels=channels,
            dtype=str(arr.dtype),
            min_val=round(min_v, 4),
            max_val=round(max_v, 4),
            mean_val=round(mean_v, 4),
            std_val=round(std_v, 4),
            nan_count=nan_count,
            inf_count=inf_count,
            dead_frames_count=dead_frames,
            is_time_monotonic=is_monotonic,
            frame_rate_hz=fps,
            duration_s=round(dur_s, 4),
            temperature_units=temp_units,
            is_radiometric=is_radiometric,
            timestamps_available=timestamps_avail,
            excitation_type=exc_type,
            excitation_metadata=exc_meta,
            fov_mm=fov,
            pixel_pitch_mm=(fov[0] / max(1, W - 1)) if fov else None,
            warnings=warnings,
            raw_metadata=meta,
            loaded_cube_k=cube_k,
            time_vector=t_vec
        )

    @staticmethod
    def _inspect_directory(dir_path: Path, meta: Dict[str, Any], warnings: List[str]) -> InputInspectionResult:
        """Inspect directory containing simulation case or image frames."""
        sim_npz = dir_path / "thermograms.npz"
        meta_json = dir_path / "metadata.json"
        
        if sim_npz.exists() and meta_json.exists():
            with open(meta_json, "r", encoding="utf-8") as f:
                dir_meta = json.load(f)
            merged_meta = {**dir_meta, **meta}
            data = np.load(sim_npz)
            cube = data["thermograms"]
            t_vec = data["time_vector"]
            merged_meta["time_vector"] = t_vec
            merged_meta["excitation"] = merged_meta.get("excitation", {"type": "lfmt"})
            merged_meta["is_simulation"] = True
            
            res = UniversalInputAnalyzer._inspect_numpy_array(cube, merged_meta, warnings, source_name=str(dir_path))
            res.input_type = InputType.SIMULATION_SEQUENCE
            return res

        # Check for image sequence in directory
        img_files = sorted([p for p in dir_path.glob("*.*") if p.suffix.lower() in (".png", ".jpg", ".tif", ".tiff", ".csv")])
        if img_files:
            return UniversalInputAnalyzer._inspect_image_stack(img_files, meta, warnings)

        warnings.append(f"No recognizable thermal sequence files found in directory {dir_path}")
        return UniversalInputAnalyzer._inspect_numpy_array(np.zeros((1, 64, 64)), meta, warnings)

    @staticmethod
    def _inspect_zip_archive(zip_path: Path, meta: Dict[str, Any], warnings: List[str]) -> InputInspectionResult:
        """Inspect zip archive containing CSV frames or TIFF stacks."""
        from lfmt.io_experimental import ExperimentalDataLoader
        try:
            fps = float(meta.get("frame_rate_hz", 25.0))
            subsample = int(meta.get("subsample_step", 1))
            seq = ExperimentalDataLoader.load_csv_zip_archive(
                zip_path=zip_path,
                frame_rate_hz=fps * subsample,
                fov_mm=meta.get("fov_mm", (150.0, 150.0)),
                temp_units=meta.get("temp_units", "C"),
                subsample_step=subsample
            )
            merged_meta = {**seq.metadata, **meta, "time_vector": seq.time_vector, "frame_rate_hz": seq.frame_rate_hz, "fov_mm": seq.fov_mm}
            res = UniversalInputAnalyzer._inspect_numpy_array(seq.surface_temperature, merged_meta, warnings, source_name=str(zip_path))
            res.input_type = InputType.CSV_SEQUENCE
            return res
        except Exception as e:
            warnings.append(f"Failed to extract CSV zip archive: {e}")
            return UniversalInputAnalyzer._inspect_numpy_array(np.zeros((1, 64, 64)), meta, warnings)

    @staticmethod
    def _inspect_numpy_file(file_path: Path, meta: Dict[str, Any], warnings: List[str]) -> InputInspectionResult:
        """Load and inspect .npy or .npz file."""
        data = np.load(file_path)
        if isinstance(data, np.lib.npyio.NpzFile):
            cube_key = "thermograms" if "thermograms" in data else ("surface_temperature" if "surface_temperature" in data else list(data.keys())[0])
            cube = np.asarray(data[cube_key], dtype=float)
            if "time_vector" in data:
                meta["time_vector"] = np.asarray(data["time_vector"], dtype=float)
        else:
            cube = np.asarray(data, dtype=float)

        res = UniversalInputAnalyzer._inspect_numpy_array(cube, meta, warnings, source_name=str(file_path))
        if res.input_type == InputType.THERMAL_SEQUENCE:
            res.input_type = InputType.NUMPY_SEQUENCE
        return res

    @staticmethod
    def _inspect_mat_file(file_path: Path, meta: Dict[str, Any], warnings: List[str]) -> InputInspectionResult:
        """Load and inspect MATLAB .mat workspace file."""
        from lfmt.io_experimental import ExperimentalDataLoader
        try:
            seq = ExperimentalDataLoader.load_mat(str(file_path))
            merged_meta = {**seq.metadata, **meta, "time_vector": seq.time_vector, "frame_rate_hz": seq.frame_rate_hz}
            res = UniversalInputAnalyzer._inspect_numpy_array(seq.surface_temperature, merged_meta, warnings, source_name=str(file_path))
            res.input_type = InputType.MAT_SEQUENCE
            return res
        except Exception as e:
            warnings.append(f"MAT parsing error: {e}")
            return UniversalInputAnalyzer._inspect_numpy_array(np.zeros((1, 64, 64)), meta, warnings)

    @staticmethod
    def _inspect_single_csv(file_path: Path, meta: Dict[str, Any], warnings: List[str]) -> InputInspectionResult:
        """Load and inspect a single CSV text matrix."""
        try:
            import pandas as pd
            arr = pd.read_csv(file_path, header=None).values.astype(float)
        except Exception:
            arr = np.genfromtxt(file_path, delimiter=",").astype(float)

        res = UniversalInputAnalyzer._inspect_numpy_array(arr, meta, warnings, source_name=str(file_path))
        res.input_type = InputType.THERMAL_SINGLE_IMAGE
        return res

    @staticmethod
    def _inspect_image_file(file_path: Path, meta: Dict[str, Any], warnings: List[str]) -> InputInspectionResult:
        """Load and inspect standard image (PNG, JPG, TIFF)."""
        import matplotlib.image as mpimg
        try:
            img = mpimg.imread(str(file_path))
            if img.ndim == 3 and img.shape[2] in (3, 4):
                # Visual RGB
                res = UniversalInputAnalyzer._inspect_numpy_array(img, meta, warnings, source_name=str(file_path))
                res.input_type = InputType.VISIBLE_IMAGE
                return res
            else:
                res = UniversalInputAnalyzer._inspect_numpy_array(img, meta, warnings, source_name=str(file_path))
                res.input_type = InputType.THERMAL_SINGLE_IMAGE
                return res
        except Exception as e:
            warnings.append(f"Image load error: {e}")
            return UniversalInputAnalyzer._inspect_numpy_array(np.zeros((64, 64)), meta, warnings)

    @staticmethod
    def _inspect_image_stack(files: List[Path], meta: Dict[str, Any], warnings: List[str]) -> InputInspectionResult:
        """Load and stack multiple image frame files."""
        frames = []
        for p in files:
            if p.suffix.lower() == ".csv":
                try:
                    import pandas as pd
                    arr = pd.read_csv(p, header=None).values.astype(float)
                except Exception:
                    arr = np.genfromtxt(p, delimiter=",").astype(float)
            else:
                import matplotlib.image as mpimg
                arr = mpimg.imread(str(p))
                if arr.ndim == 3:
                    arr = np.mean(arr[:, :, :3], axis=2)
            frames.append(arr)

        cube = np.stack(frames, axis=0)
        return UniversalInputAnalyzer._inspect_numpy_array(cube, meta, warnings, source_name="image_stack")

    @staticmethod
    def _infer_representation(
        min_v: float,
        max_v: float,
        input_type: InputType,
        meta: Dict[str, Any],
        warnings: List[str]
    ) -> Tuple[DataRepresentation, str, bool, str, Optional[float], Optional[Tuple[float, float]]]:
        """Infer representation type, units, radiometric status, excitation, and geometry."""
        rep = DataRepresentation.UNKNOWN
        units = meta.get("temp_units", meta.get("units", "UNKNOWN")).upper()
        is_radiometric = False
        exc_type = meta.get("excitation_type", meta.get("excitation", {}).get("type", "unknown")).lower()
        fps = meta.get("frame_rate_hz", meta.get("fps"))
        if fps is not None:
            fps = float(fps)
        fov = meta.get("fov_mm")
        if fov is not None and len(fov) == 2:
            fov = (float(fov[0]), float(fov[1]))

        if input_type == InputType.VISIBLE_IMAGE:
            return DataRepresentation.VISIBLE_RGB, "NORMALIZED", False, "none", None, None

        if units in ("K", "KELVIN"):
            rep = DataRepresentation.RADIOMETRIC_TEMPERATURE
            units = "K"
            is_radiometric = True
        elif units in ("C", "CELSIUS"):
            rep = DataRepresentation.RADIOMETRIC_TEMPERATURE
            units = "C"
            is_radiometric = True
        else:
            # Numerical heuristic
            if 200.0 <= min_v and max_v <= 600.0:
                rep = DataRepresentation.RADIOMETRIC_TEMPERATURE
                units = "K"
                is_radiometric = True
                warnings.append("Temperature units inferred as Kelvin based on range [200, 600] K.")
            elif -40.0 <= min_v and max_v <= 350.0:
                rep = DataRepresentation.RADIOMETRIC_TEMPERATURE
                units = "C"
                is_radiometric = True
                warnings.append("Temperature units inferred as Celsius based on range [-40, 350] °C.")
            elif 0.0 <= min_v and max_v <= 1.0:
                rep = DataRepresentation.NORMALIZED_INTENSITY
                units = "NORMALIZED"
                warnings.append("Data is normalized in [0, 1]. Absolute thermodynamic physics is disabled.")
            elif 0 <= min_v and max_v > 1000 and max_v <= 65535:
                rep = DataRepresentation.RAW_SENSOR_COUNTS
                units = "RAW_COUNTS"
                warnings.append("Data contains raw 14/16-bit sensor counts without radiometric calibration.")
            else:
                rep = DataRepresentation.UNKNOWN
                units = "UNKNOWN"
                warnings.append("Uncalibrated numerical span. Physical thermal equations are blocked.")

        return rep, units, is_radiometric, exc_type, fps, fov
