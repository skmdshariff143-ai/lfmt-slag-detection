"""
Virtual Infrared Camera Module.

Simulates an IR camera sensor capturing surface radiation, spatial pixel projection,
framerate sampling, optical resolution interpolation, and exact ground-truth mask synthesis.
"""

from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import numpy as np
from scipy.interpolate import RegularGridInterpolator

from lfmt.config import LFMTConfig, CameraConfig
from lfmt.simulation.base import SimulationResult, GroundTruth


@dataclass
class VirtualCameraCapture:
    """
    Captured thermogram sequence and spatial ground truth.

    Attributes:
        thermograms: 3D array of surface temperatures T(time, height, width) [K].
        time_vector: 1D time vector [s].
        ground_truth_mask: 2D binary mask of defect on camera grid (height, width).
        ground_truth: GroundTruth metadata object.
        camera_config: Camera configuration settings.
        metadata: Camera simulation metadata.
    """
    thermograms: np.ndarray        # shape: (n_frames, H, W)
    time_vector: np.ndarray        # shape: (n_frames,)
    ground_truth_mask: np.ndarray  # shape: (H, W), dtype bool or int
    ground_truth: GroundTruth
    camera_config: CameraConfig
    metadata: Dict[str, Any]

    @property
    def height(self) -> int:
        return self.thermograms.shape[1]

    @property
    def width(self) -> int:
        return self.thermograms.shape[2]

    @property
    def n_frames(self) -> int:
        return self.thermograms.shape[0]

    def save_case(self, output_dir: str | Path, case_id: str = "case_0001") -> Path:
        """
        Save captured sequence to standard dataset directory format.

        Structure:
            output_dir/case_id/
                thermograms.npz
                metadata.json
                ground_truth_mask.npy
        """
        case_path = Path(output_dir) / case_id
        case_path.mkdir(parents=True, exist_ok=True)

        # 1. Save thermogram tensor (compressed)
        np.savez_compressed(
            case_path / "thermograms.npz",
            thermograms=self.thermograms.astype(np.float32),
            time_vector=self.time_vector.astype(np.float32)
        )

        # 2. Save ground truth mask
        np.save(case_path / "ground_truth_mask.npy", self.ground_truth_mask.astype(np.uint8))

        # 3. Save JSON metadata
        meta_dict = {
            "case_id": case_id,
            "tensor_shape": list(self.thermograms.shape),
            "time_duration_s": float(self.time_vector[-1] - self.time_vector[0]),
            "fps": float(self.camera_config.sampling_rate_hz),
            "resolution": [self.height, self.width],
            "ground_truth": self.ground_truth.to_dict(),
            "camera_metadata": self.metadata,
        }

        with open(case_path / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta_dict, f, indent=2)

        return case_path

    @classmethod
    def load_case(cls, case_dir: str | Path) -> VirtualCameraCapture:
        """Load saved thermogram dataset case."""
        case_path = Path(case_dir)
        data = np.load(case_path / "thermograms.npz")
        thermograms = data["thermograms"]
        time_vector = data["time_vector"]
        gt_mask = np.load(case_path / "ground_truth_mask.npy").astype(bool)

        with open(case_path / "metadata.json", "r", encoding="utf-8") as f:
            meta = json.load(f)

        gt_info = meta["ground_truth"]
        gt = GroundTruth(
            center_x_mm=gt_info["center_x_mm"],
            center_y_mm=gt_info["center_y_mm"],
            depth_mm=gt_info["depth_mm"],
            diameter_mm=gt_info["diameter_mm"],
            thickness_mm=gt_info["thickness_mm"],
            material_name=gt_info["material_name"],
            area_mm2=gt_info["area_mm2"],
            volume_mm3=gt_info["volume_mm3"],
            has_defect=gt_info.get("has_defect", True),
        )

        cam_cfg = CameraConfig(
            resolution_x=thermograms.shape[2],
            resolution_y=thermograms.shape[1],
            sampling_rate_hz=meta.get("fps", 10.0),
        )

        return cls(
            thermograms=thermograms,
            time_vector=time_vector,
            ground_truth_mask=gt_mask,
            ground_truth=gt,
            camera_config=cam_cfg,
            metadata=meta.get("camera_metadata", {}),
        )


class VirtualIRCamera:
    """
    Simulated Infrared Focal Plane Array (FPA) Camera Sensor.
    """

    def __init__(self, camera_config: CameraConfig):
        self.config = camera_config

    def capture(self, sim_result: SimulationResult) -> VirtualCameraCapture:
        """
        Project simulation surface temperature to camera sensor grid.
        """
        raw_surf = sim_result.surface_temperature  # (n_sim_frames, ny_sim, nx_sim)
        t_sim = sim_result.time_vector
        x_sim = sim_result.x_grid_mm
        y_sim = sim_result.y_grid_mm

        H = self.config.resolution_y
        W = self.config.resolution_x
        fps = self.config.sampling_rate_hz

        # Camera spatial coordinate grids (spanning plate dimensions)
        x_cam_mm = np.linspace(x_sim[0], x_sim[-1], W)
        y_cam_mm = np.linspace(y_sim[0], y_sim[-1], H)

        # Time resampling if camera FPS differs from simulation sampling
        t_duration = t_sim[-1] - t_sim[0]
        n_cam_frames = int(round(t_duration * fps)) + 1
        t_cam = np.linspace(t_sim[0], t_sim[-1], n_cam_frames)

        # Interpolate spatially for each frame
        # RegularGridInterpolator on (t, y, x) or frame-by-frame 2D interpolation
        interpolator = RegularGridInterpolator(
            (t_sim, y_sim, x_sim),
            raw_surf,
            method="linear",
            bounds_error=False,
            fill_value=None
        )

        # Construct meshgrid for camera evaluation points
        TT, YY, XX = np.meshgrid(t_cam, y_cam_mm, x_cam_mm, indexing="ij")
        pts = np.stack([TT.ravel(), YY.ravel(), XX.ravel()], axis=-1)
        thermograms = interpolator(pts).reshape((n_cam_frames, H, W))

        # Generate exact ground-truth mask on camera pixel grid
        gt = sim_result.ground_truth
        X_cam_2d, Y_cam_2d = np.meshgrid(x_cam_mm, y_cam_mm, indexing="xy")
        dist_sq = (X_cam_2d - gt.center_x_mm) ** 2 + (Y_cam_2d - gt.center_y_mm) ** 2
        gt_mask = dist_sq <= (gt.diameter_mm / 2.0) ** 2

        # Pixel dimensions
        dx_mm_px = (x_cam_mm[-1] - x_cam_mm[0]) / max(1, (W - 1))
        dy_mm_px = (y_cam_mm[-1] - y_cam_mm[0]) / max(1, (H - 1))

        metadata = {
            "sensor_resolution": [H, W],
            "pixel_pitch_x_mm": float(dx_mm_px),
            "pixel_pitch_y_mm": float(dy_mm_px),
            "fps": fps,
            "fov_mm": [float(x_sim[-1] - x_sim[0]), float(y_sim[-1] - y_sim[0])],
            "gt_pixel_area": int(np.sum(gt_mask)),
        }

        return VirtualCameraCapture(
            thermograms=thermograms,
            time_vector=t_cam,
            ground_truth_mask=gt_mask,
            ground_truth=gt,
            camera_config=self.config,
            metadata=metadata
        )
