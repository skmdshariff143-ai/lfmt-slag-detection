"""
FastAPI Routes for MATLAB FDM and Python FEM Simulations, Anomaly Analysis, and Cross-Validation.
"""

from __future__ import annotations
import uuid
import time
import numpy as np
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from lfmt.config import load_config
from lfmt.simulation.factory import SimulationBackendFactory
from lfmt.simulation.fem import FEMBackend
from lfmt.simulation.matlab_backend import MATLABFDMBackend
from lfmt.matlab.environment import detect_matlab_environment
from lfmt.analysis.analyzer import AutoDefectAnalyzer

router = APIRouter(prefix="/simulate", tags=["3-D Thermal Simulation"])

# Global in-memory cache for simulation runs
SIMULATION_CACHE: Dict[str, Dict[str, Any]] = {}
ANALYZER_INSTANCE = AutoDefectAnalyzer()


class DefectParam(BaseModel):
    diameter_mm: float = 8.0
    depth_mm: float = 0.4
    thickness_mm: float = 0.4
    center_x_mm: float = 50.0
    center_y_mm: float = 35.0
    material: str = "slag"


class SimulationRequest(BaseModel):
    backend: str = Field(default="matlab_fdm", description="'matlab_fdm' or 'python_fem'")
    preset: Optional[str] = Field(default="shallow_slag", description="'healthy', 'shallow_slag', 'deep_slag', 'multi_slag', or 'custom'")
    length_mm: float = 100.0
    width_mm: float = 70.0
    thickness_mm: float = 2.3
    f0_hz: float = 0.05
    f1_hz: float = 0.50
    duration_s: float = 10.0
    q0_w_m2: float = 5000.0
    camera_sampling_rate_hz: float = 10.0
    defects: Optional[List[DefectParam]] = None
    spatial_resolution: Optional[Dict[str, int]] = None
    timestep_s: float = 0.04
    run_analyzer: bool = True


def _run_simulation_task(run_id: str, req: SimulationRequest):
    """Execute simulation in background and populate cache."""
    try:
        SIMULATION_CACHE[run_id]["status"] = "VALIDATING_INPUT"
        SIMULATION_CACHE[run_id]["stage"] = "VALIDATING INPUT"

        # 1. Physical Geometry Validation
        if req.length_mm <= 0 or req.width_mm <= 0 or req.thickness_mm <= 0:
            raise ValueError("INVALID_GEOMETRY: Plate dimensions must be strictly positive.")

        cfg = load_config("configs/research_v3_high_fidelity.yaml")
        cfg.geometry.plate.length_mm = req.length_mm
        cfg.geometry.plate.width_mm = req.width_mm
        cfg.geometry.plate.thickness_mm = req.thickness_mm
        cfg.excitation.f0_hz = req.f0_hz
        cfg.excitation.f1_hz = req.f1_hz
        cfg.excitation.duration_s = req.duration_s
        cfg.excitation.q0_w_m2 = req.q0_w_m2
        cfg.simulation.timestep_s = req.timestep_s
        cfg.simulation.total_time_s = req.duration_s
        cfg.camera.sampling_rate_hz = req.camera_sampling_rate_hz

        # 2. Defect Configuration (Presets vs Custom)
        if req.preset == "healthy":
            cfg.geometry.inclusion.diameter_mm = 0.0
            cfg.geometry.inclusion.thickness_mm = 0.0
            cfg.geometry.inclusion.inclusions_list = []
            defects_list = []
        elif req.preset == "shallow_slag":
            cfg.geometry.inclusion.diameter_mm = 8.0
            cfg.geometry.inclusion.depth_mm = 0.4
            cfg.geometry.inclusion.thickness_mm = 0.40
            cfg.geometry.inclusion.center_x_mm = 50.0
            cfg.geometry.inclusion.center_y_mm = 35.0
            defects_list = [{"diameter_mm": 8.0, "depth_mm": 0.4, "thickness_mm": 0.40, "center_x_mm": 50.0, "center_y_mm": 35.0, "material": "slag"}]
            cfg.geometry.inclusion.inclusions_list = defects_list
        elif req.preset == "deep_slag":
            cfg.geometry.inclusion.diameter_mm = 8.0
            cfg.geometry.inclusion.depth_mm = 0.8
            cfg.geometry.inclusion.thickness_mm = 0.40
            cfg.geometry.inclusion.center_x_mm = 50.0
            cfg.geometry.inclusion.center_y_mm = 35.0
            defects_list = [{"diameter_mm": 8.0, "depth_mm": 0.8, "thickness_mm": 0.40, "center_x_mm": 50.0, "center_y_mm": 35.0, "material": "slag"}]
            cfg.geometry.inclusion.inclusions_list = defects_list
        elif req.preset == "multi_slag":
            defects_list = [
                {"diameter_mm": 6.0, "depth_mm": 0.4, "thickness_mm": 0.40, "center_x_mm": 42.5, "center_y_mm": 35.0, "material": "slag"},
                {"diameter_mm": 4.8, "depth_mm": 0.4, "thickness_mm": 0.40, "center_x_mm": 57.5, "center_y_mm": 35.0, "material": "slag"}
            ]
            cfg.geometry.inclusion.diameter_mm = 6.0
            cfg.geometry.inclusion.depth_mm = 0.4
            cfg.geometry.inclusion.thickness_mm = 0.40
            cfg.geometry.inclusion.center_x_mm = 42.5
            cfg.geometry.inclusion.center_y_mm = 35.0
            cfg.geometry.inclusion.inclusions_list = defects_list
        else:
            # Custom Mode: req.defects is strictly authoritative
            if req.defects and len(req.defects) > 0:
                defects_list = [d.model_dump() if hasattr(d, "model_dump") else d.dict() for d in req.defects]
                d0 = req.defects[0]
                cfg.geometry.inclusion.diameter_mm = d0.diameter_mm
                cfg.geometry.inclusion.depth_mm = d0.depth_mm
                cfg.geometry.inclusion.thickness_mm = d0.thickness_mm
                cfg.geometry.inclusion.center_x_mm = d0.center_x_mm
                cfg.geometry.inclusion.center_y_mm = d0.center_y_mm
                cfg.geometry.inclusion.inclusions_list = defects_list
            else:
                cfg.geometry.inclusion.diameter_mm = 0.0
                cfg.geometry.inclusion.thickness_mm = 0.0
                cfg.geometry.inclusion.inclusions_list = []
                defects_list = []

        # Validate defect depth
        for d in defects_list:
            if d["depth_mm"] < 0 or (d["depth_mm"] + d["thickness_mm"]) > req.thickness_mm:
                raise ValueError(
                    f"INVALID_DEFECT_DEPTH: Defect depth ({d['depth_mm']} mm) + thickness "
                    f"({d['thickness_mm']} mm) exceeds plate thickness ({req.thickness_mm} mm)."
                )

        if req.spatial_resolution:
            cfg.simulation.spatial_resolution = req.spatial_resolution

        SIMULATION_CACHE[run_id]["status"] = "SOLVING"
        SIMULATION_CACHE[run_id]["stage"] = "Solving 3-D Heat Equation..."

        # 3. Instantiate requested backend
        try:
            backend = SimulationBackendFactory.create(req.backend)
            sim_res = backend.run(cfg)
        except RuntimeError as re:
            err_str = str(re)
            if "MATLAB_ENGINE_UNAVAILABLE" in err_str:
                raise RuntimeError(err_str)
            elif "MATLAB_SIMULATION_FAILED" in err_str:
                raise RuntimeError(err_str)
            else:
                raise RuntimeError(f"SIMULATION_FAILED: {err_str}")

        SIMULATION_CACHE[run_id]["status"] = "ANALYZING"
        SIMULATION_CACHE[run_id]["stage"] = "Running Thermographic NDT Analysis..."

        # 4. Extract temperature arrays
        surf_temp = sim_res.surface_temperature  # (n_cam_frames, 28, 40)
        time_vec = sim_res.time_vector
        Tamb = cfg.excitation.ambient_temp_k
        delta_T = surf_temp - Tamb

        # Probe points: Defect center (14, 20), Reference corner (4, 4), Plate Mean
        center_curve = [float(val) for val in delta_T[:, 14, 20]]
        reference_curve = [float(val) for val in delta_T[:, 4, 4]]
        mean_curve = [float(val) for val in np.mean(delta_T, axis=(1, 2))]

        # Downsample animation frames for lightweight web transmission if needed
        step = 1 if len(time_vec) <= 120 else 2
        anim_frames = surf_temp[::step].round(3).tolist()
        anim_delta_t = delta_T[::step].round(3).tolist()
        anim_times = [float(t) for t in time_vec[::step]]

        # 5. Run AutoDefectAnalyzer if requested
        analysis_data = None
        if req.run_analyzer:
            try:
                ana_res = ANALYZER_INSTANCE.analyze(
                    source=surf_temp,
                    metadata_override={
                        "source_type": backend.backend_type.upper(),
                        "frame_rate_hz": float(req.camera_sampling_rate_hz),
                        "excitation_type": "LFMT_CHIRP"
                    }
                )
                analysis_data = ana_res.to_dict()
            except Exception as ae:
                raise RuntimeError(f"ANALYZER_FAILED: Autonomous defect analyzer error - {str(ae)}")

        SIMULATION_CACHE[run_id]["status"] = "COMPLETED"
        SIMULATION_CACHE[run_id]["stage"] = "Simulation and Analysis Complete"
        SIMULATION_CACHE[run_id]["result"] = {
            "run_id": run_id,
            "backend": req.backend,
            "solver_name": sim_res.metadata.get("solver_name", sim_res.backend_name),
            "discretization_method": sim_res.metadata.get("discretization_method", "Finite Element / Difference"),
            "execution_time_s": float(sim_res.metadata.get("execution_time_s", 0.0)),
            "solver_dt_s": float(sim_res.metadata.get("solver_dt_s", req.timestep_s)),
            "camera_frame_rate_hz": float(sim_res.metadata.get("camera_frame_rate_hz", req.camera_sampling_rate_hz)),
            "ambient_temp_k": float(Tamb),
            "peak_delta_t_k": float(np.max(delta_T)),
            "max_temp_k": float(np.max(surf_temp)),
            "min_temp_k": float(np.min(surf_temp)),
            "time_vector": anim_times,
            "animation": {
                "surface_temperature": anim_frames,
                "delta_t": anim_delta_t,
                "n_frames": len(anim_frames),
                "grid_shape": [surf_temp.shape[1], surf_temp.shape[2]],
                "x_coords_mm": [float(x) for x in sim_res.x_grid_mm],
                "y_coords_mm": [float(y) for y in sim_res.y_grid_mm]
            },
            "temperature_curves": {
                "time_s": [float(t) for t in time_vec],
                "probe_roi_dT": center_curve,
                "defect_center_roi_dT": center_curve,
                "reference_roi_dT": reference_curve,
                "sound_plate_roi_dT": reference_curve,
                "plate_mean_dT": mean_curve
            },
            "ground_truth": {
                "has_defect": len(defects_list) > 0,
                "defects": defects_list
            },
            "analysis_result": analysis_data
        }
    except Exception as e:
        SIMULATION_CACHE[run_id]["status"] = "FAILED"
        SIMULATION_CACHE[run_id]["stage"] = f"Error: {str(e)}"
        SIMULATION_CACHE[run_id]["error"] = str(e)


@router.get("/backends")
async def get_simulation_backends():
    """Return status of available simulation engines."""
    matlab_env = detect_matlab_environment()
    return {
        "python_fem": {
            "status": "AVAILABLE",
            "name": "Python 3-D Hexahedral FEM",
            "engine": "scikit-fem (ElementHex1)"
        },
        "matlab_fdm": {
            "status": "AVAILABLE" if matlab_env["matlab_available"] else "UNAVAILABLE",
            "name": "MATLAB 3-D Conservative FDM",
            "engine": matlab_env.get("release", "R2026a"),
            "connection_mode": matlab_env.get("recommended_mode", "engine"),
            "details": matlab_env
        }
    }


@router.post("")
async def start_simulation(req: SimulationRequest, background_tasks: BackgroundTasks):
    """Start a 3-D thermal simulation run."""
    run_id = f"sim_{uuid.uuid4().hex[:12]}"
    SIMULATION_CACHE[run_id] = {
        "run_id": run_id,
        "backend": req.backend,
        "preset": req.preset,
        "status": "QUEUED",
        "stage": "Job queued in simulation worker...",
        "created_at": time.time(),
        "result": None
    }
    background_tasks.add_task(_run_simulation_task, run_id, req)
    return {
        "run_id": run_id,
        "status": "QUEUED",
        "message": f"Simulation job '{run_id}' dispatched to {req.backend} worker."
    }


@router.get("/{run_id}")
async def get_simulation_status(run_id: str):
    """Get status of a simulation job."""
    if run_id not in SIMULATION_CACHE:
        raise HTTPException(status_code=404, detail=f"Simulation job '{run_id}' not found.")
    job = SIMULATION_CACHE[run_id]
    return {
        "run_id": run_id,
        "backend": job["backend"],
        "status": job["status"],
        "stage": job["stage"],
        "has_result": job["result"] is not None
    }


@router.get("/{run_id}/result")
async def get_simulation_result(run_id: str):
    """Get full simulation results, animation frames, curves, and analysis verdict."""
    if run_id not in SIMULATION_CACHE:
        raise HTTPException(status_code=404, detail=f"Simulation job '{run_id}' not found.")
    job = SIMULATION_CACHE[run_id]
    if job["status"] == "FAILED":
        raise HTTPException(status_code=500, detail=job.get("error", "Simulation failed."))
    if job["result"] is None:
        return JSONResponse(status_code=202, content={"status": job["status"], "stage": job["stage"]})
    return JSONResponse(content=job["result"])


@router.post("/compare")
async def compare_simulation_backends(preset: str = "shallow_slag"):
    """Run Python FEM and MATLAB FDM side-by-side on identical configuration."""
    cfg = load_config("configs/research_v3_high_fidelity.yaml")
    cfg.camera.sampling_rate_hz = 10.0
    cfg.simulation.timestep_s = 0.04

    if preset == "healthy":
        cfg.geometry.inclusion.diameter_mm = 0.0
        cfg.geometry.inclusion.depth_mm = 0.0
        cfg.geometry.inclusion.inclusions_list = []
    elif preset == "shallow_slag":
        cfg.geometry.inclusion.diameter_mm = 8.0
        cfg.geometry.inclusion.depth_mm = 0.4
        cfg.geometry.inclusion.thickness_mm = 0.40
        cfg.geometry.inclusion.inclusions_list = [{"diameter_mm": 8.0, "depth_mm": 0.4, "thickness_mm": 0.40, "center_x_mm": 50.0, "center_y_mm": 35.0, "material": "slag"}]
    elif preset == "deep_slag":
        cfg.geometry.inclusion.diameter_mm = 8.0
        cfg.geometry.inclusion.depth_mm = 0.8
        cfg.geometry.inclusion.thickness_mm = 0.40
        cfg.geometry.inclusion.inclusions_list = [{"diameter_mm": 8.0, "depth_mm": 0.8, "thickness_mm": 0.40, "center_x_mm": 50.0, "center_y_mm": 35.0, "material": "slag"}]

    fem_b = FEMBackend()
    matlab_b = MATLABFDMBackend(mode="engine")

    t0 = time.perf_counter()
    fem_res = fem_b.run(cfg)
    fem_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    matlab_res = matlab_b.run(cfg)
    matlab_time = time.perf_counter() - t0

    Tamb = cfg.excitation.ambient_temp_k
    dT_fem = fem_res.surface_temperature - Tamb
    dT_fdm = matlab_res.surface_temperature - Tamb

    l2_diff = float(np.linalg.norm(dT_fdm - dT_fem))
    l2_ref = float(np.linalg.norm(dT_fem))
    rel_l2_pct = (l2_diff / max(1e-12, l2_ref)) * 100.0

    peak_fem = float(np.max(dT_fem))
    peak_fdm = float(np.max(dT_fdm))
    peak_diff = abs(peak_fdm - peak_fem)

    import scipy.stats
    r_spatial, _ = scipy.stats.pearsonr(
        dT_fem[int(0.8 * len(fem_res.time_vector))].flatten(),
        dT_fdm[int(0.8 * len(matlab_res.time_vector))].flatten()
    )

    return {
        "preset": preset,
        "python_fem": {
            "solver": "Python 3-D Hexahedral FEM",
            "peak_delta_t_k": peak_fem,
            "runtime_s": float(fem_time)
        },
        "matlab_fdm": {
            "solver": "MATLAB 3-D Conservative FDM",
            "peak_delta_t_k": peak_fdm,
            "runtime_s": float(matlab_time)
        },
        "comparison_metrics": {
            "rel_l2_error_pct": float(rel_l2_pct),
            "peak_delta_t_diff_k": float(peak_diff),
            "spatial_correlation": float(r_spatial),
            "target_l2_threshold_pct": 5.0,
            "is_cross_validated": bool(rel_l2_pct <= 5.0)
        }
    }


@router.get("/precomputed")
async def get_precomputed_matlab_result():
    """Return precomputed verified MATLAB numerical simulation result for shallow_slag."""
    import json
    from pathlib import Path
    repo_root = Path(__file__).resolve().parent.parent.parent
    pre_path = repo_root / "data" / "precomputed" / "matlab_shallow_slag.json"
    if not pre_path.exists():
        raise HTTPException(status_code=404, detail="Precomputed MATLAB simulation file not found.")
    with open(pre_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return JSONResponse(content=data)


