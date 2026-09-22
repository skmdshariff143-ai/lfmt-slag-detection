r"""
MATLAB 3-D Conservative Finite Difference (FDM) Simulation Backend (Research V3).

Scientific Identifier: matlab_fdm
Governing Equation: \rho(x) C_p(x) \partial T / \partial t = \nabla \cdot (k(x) \nabla T)
Discretization: 3-D Conservative Flux Finite Difference with Harmonic Interface Conductivity
Time Integration: Implicit Backward Euler
"""

from __future__ import annotations
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Optional, List, Dict
import numpy as np

try:
    import matlab
    import matlab.engine
    MATLAB_ENGINE_INSTALLED = True
except ImportError:
    MATLAB_ENGINE_INSTALLED = False

from lfmt.config import LFMTConfig
from lfmt.simulation.base import ThermalSimulationBackend, SimulationResult, GroundTruth
from lfmt.matlab.environment import detect_matlab_environment

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class MATLABFDMBackend(ThermalSimulationBackend):
    """
    MATLAB 3-D Conservative Finite Difference Transient Heat Conduction Backend.
    """

    def __init__(self, mode: Optional[str] = None):
        self.env_info = detect_matlab_environment()
        self.mode = mode or self.env_info.get("recommended_mode", "batch")
        self._engine: Optional[Any] = None

    @property
    def backend_type(self) -> str:
        return "matlab_fdm"

    @property
    def is_fem(self) -> bool:
        # Strictly return False to uphold scientific non-overclaiming rules
        return False

    @property
    def is_engine_available(self) -> bool:
        return self.env_info.get("matlab_available", False)

    @property
    def engine_name(self) -> str:
        return f"MATLAB_FDM ({self.env_info.get('release', 'R2026a')} 3-D Conservative FDM)"

    @classmethod
    def detect(cls) -> Dict[str, Any]:
        """Detect local MATLAB installation and runtime capabilities."""
        return detect_matlab_environment()

    def health_check(self) -> bool:
        """Verify MATLAB backend is responsive and operational."""
        try:
            if self.mode == "engine" and MATLAB_ENGINE_INSTALLED:
                self.start_engine()
                if self._engine is not None:
                    res = self._engine.eval("1+1", nargout=1)
                    return int(res) == 2
            return bool(self.env_info.get("matlab_available", False))
        except Exception:
            return False

    def start_engine(self):
        """Initialize persistent MATLAB Engine session if not already running."""
        if self.mode == "engine" and MATLAB_ENGINE_INSTALLED and self._engine is None:
            self._engine = matlab.engine.start_matlab()
            repo_matlab = str((REPO_ROOT / "matlab").resolve())
            self._engine.addpath(repo_matlab, nargout=0)

    def stop_engine(self):
        """Terminate active MATLAB Engine session."""
        if self._engine is not None:
            try:
                self._engine.quit()
            except Exception:
                pass
            self._engine = None

    def __del__(self):
        self.stop_engine()

    def run(self, config: LFMTConfig) -> SimulationResult:
        """
        Execute 3-D transient heat simulation in MATLAB.
        """
        if not self.env_info.get("matlab_available", False):
            raise RuntimeError(
                "MATLAB_ENGINE_UNAVAILABLE: MATLAB executable or engine is not found on this system."
            )

        # 1. Build standardized dictionary for MATLAB config
        Lx_mm = float(config.geometry.plate.length_mm)
        Ly_mm = float(config.geometry.plate.width_mm)
        Lz_mm = float(config.geometry.plate.thickness_mm)

        nx = int(config.simulation.spatial_resolution.get("nx", 40))
        ny = int(config.simulation.spatial_resolution.get("ny", 28))
        nz = int(config.simulation.spatial_resolution.get("nz", 12))
        dt = float(config.simulation.timestep_s)
        total_time = float(config.simulation.total_time_s)
        cam_fps = float(getattr(config.camera, "sampling_rate_hz", 10.0))

        f0 = float(config.excitation.f0_hz)
        f1 = float(config.excitation.f1_hz)
        q0 = float(config.excitation.q0_w_m2)
        duration = float(config.excitation.duration_s)
        h_conv = float(config.excitation.h_conv_w_m2k)
        Tamb = float(config.excitation.ambient_temp_k)

        inc = config.geometry.inclusion
        defects_list: List[Dict[str, Any]] = []

        if inc.inclusions_list and len(inc.inclusions_list) > 0:
            for d in inc.inclusions_list:
                defects_list.append({
                    "diameter_mm": float(d.get("diameter_mm", 0.0)),
                    "depth_mm": float(d.get("depth_mm", 0.0)),
                    "thickness_mm": float(d.get("thickness_mm", 0.0)),
                    "center_x_mm": float(d.get("center_x_mm", 50.0)),
                    "center_y_mm": float(d.get("center_y_mm", 35.0)),
                    "material": str(d.get("material", "slag"))
                })
        elif inc.diameter_mm > 0 and inc.thickness_mm > 0:
            defects_list.append({
                "diameter_mm": float(inc.diameter_mm),
                "depth_mm": float(inc.depth_mm),
                "thickness_mm": float(inc.thickness_mm),
                "center_x_mm": float(inc.center_x_mm),
                "center_y_mm": float(inc.center_y_mm),
                "material": str(inc.material)
            })

        has_defect = len(defects_list) > 0

        matlab_cfg_dict = {
            "plate": {"length_mm": Lx_mm, "width_mm": Ly_mm, "thickness_mm": Lz_mm},
            "simulation": {"Nx": nx, "Ny": ny, "Nz": nz, "dt_s": dt, "total_time_s": total_time},
            "excitation": {
                "f0_hz": f0, "f1_hz": f1, "q0_w_m2": q0,
                "duration_s": duration, "h_conv_w_m2k": h_conv, "ambient_temp_k": Tamb
            },
            "camera": {
                "cam_nx": int(getattr(config.camera, "resolution_x", 40)),
                "cam_ny": int(getattr(config.camera, "resolution_y", 28)),
                "frame_rate_hz": cam_fps
            },
            "defects": defects_list
        }

        # 2. Execution via MATLAB Engine (Mode A) or Batch Process (Mode B)
        if self.mode == "engine" and MATLAB_ENGINE_INSTALLED:
            self.start_engine()
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as f_json:
                json.dump(matlab_cfg_dict, f_json)
                json_path = f_json.name

            try:
                res_struct = self._engine.lfmt.solveTransientThermal(json_path)
                
                # Extract surface temperature array: MATLAB [N_frames, 28, 40]
                surf_mat = res_struct["surface_temperature"]
                surface_temp = np.array(surf_mat, dtype=np.float64)
                
                t_vec_mat = res_struct["time_vector"]
                time_vector = np.array(t_vec_mat, dtype=np.float64).flatten()
                
                cam_x = np.array(res_struct["camera_x_mm"], dtype=np.float64).flatten()
                cam_y = np.array(res_struct["camera_y_mm"], dtype=np.float64).flatten()
                runtime_s = float(res_struct["runtime_s"])
            except Exception as e:
                raise RuntimeError(f"MATLAB_SIMULATION_FAILED: {str(e)}") from e
            finally:
                Path(json_path).unlink(missing_ok=True)
        else:
            # Mode B: Batch Execution
            with tempfile.TemporaryDirectory() as tmpdir:
                json_path = str(Path(tmpdir) / "config.json")
                mat_out_path = str(Path(tmpdir) / "output.mat")
                
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(matlab_cfg_dict, f)
                
                matlab_exe = os.environ.get("LFMT_MATLAB_EXECUTABLE") or self.env_info.get("matlab_path")
                if not matlab_exe:
                    raise RuntimeError("MATLAB_ENGINE_UNAVAILABLE: No MATLAB executable detected.")
                
                cmd = [
                    matlab_exe, "-batch",
                    f"addpath('matlab'); run_lfmt_from_json('{json_path}', '{mat_out_path}'); exit;"
                ]
                import subprocess
                try:
                    subprocess.run(cmd, check=True, cwd=str(REPO_ROOT))
                except Exception as e:
                    raise RuntimeError(f"MATLAB_SIMULATION_FAILED: Batch solver error - {str(e)}") from e
                
                import scipy.io
                mat_data = scipy.io.loadmat(mat_out_path)
                surface_temp = np.array(mat_data["surface_temperature"], dtype=np.float64)
                time_vector = np.array(mat_data["time_vector"], dtype=np.float64).flatten()
                cam_x = np.array(mat_data["camera_x_mm"], dtype=np.float64).flatten()
                cam_y = np.array(mat_data["camera_y_mm"], dtype=np.float64).flatten()
                runtime_s = float(mat_data["runtime_s"][0, 0])

        # Sizing / Volume for primary defect
        primary_d = defects_list[0] if has_defect else {}
        d_diam = float(primary_d.get("diameter_mm", 0.0))
        d_thick = float(primary_d.get("thickness_mm", 0.0))
        d_depth = float(primary_d.get("depth_mm", 0.0))
        d_cx = float(primary_d.get("center_x_mm", 50.0))
        d_cy = float(primary_d.get("center_y_mm", 35.0))
        d_mat = str(primary_d.get("material", "slag"))

        gt_area = math.pi * (d_diam / 2.0)**2 if has_defect else 0.0
        gt_vol = gt_area * d_thick if has_defect else 0.0

        gt = GroundTruth(
            center_x_mm=d_cx,
            center_y_mm=d_cy,
            depth_mm=d_depth,
            diameter_mm=d_diam,
            thickness_mm=d_thick,
            material_name=d_mat,
            area_mm2=float(gt_area),
            volume_mm3=float(gt_vol),
            has_defect=has_defect
        )

        return SimulationResult(
            surface_temperature=surface_temp,
            time_vector=time_vector,
            x_grid_mm=cam_x,
            y_grid_mm=cam_y,
            z_grid_mm=np.linspace(0, Lz_mm, nz),
            ground_truth=gt,
            backend_name="matlab_fdm",
            metadata={
                "solver_backend": "matlab_fdm",
                "solver_name": "MATLAB_FDM",
                "discretization_method": "3-D Conservative Finite Difference",
                "execution_time_s": runtime_s,
                "matlab_release": self.env_info.get("release", "R2026a"),
                "time_integration": "Implicit Backward Euler",
                "solver_dt_s": dt,
                "camera_frame_rate_hz": cam_fps,
                "grid_cells": [nx, ny, nz],
                "defects_simulated": len(defects_list)
            }
        )

