import sys
import os
import json
import time
from pathlib import Path
import numpy as np
import scipy.stats

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
if str(repo_root / "src") not in sys.path:
    sys.path.insert(0, str(repo_root / "src"))

from lfmt.config import load_config, LFMTConfig
from lfmt.simulation.fem import FEMBackend
from lfmt.simulation.matlab_backend import MATLABFDMBackend
from lfmt.analysis.analyzer import AutoDefectAnalyzer


def compute_cross_validation_metrics(T_fem: np.ndarray, T_fdm: np.ndarray, t_vec: np.ndarray, Tamb: float = 293.15):
    dT_fem = T_fem - Tamb
    dT_fdm = T_fdm - Tamb

    l2_diff = np.linalg.norm(dT_fdm - dT_fem)
    l2_ref = np.linalg.norm(dT_fem)
    rel_l2_pct = (l2_diff / max(1e-12, l2_ref)) * 100.0

    peak_fem = float(np.max(dT_fem))
    peak_fdm = float(np.max(dT_fdm))
    peak_diff = abs(peak_fdm - peak_fem)
    peak_rel_err_pct = (peak_diff / max(1e-6, peak_fem)) * 100.0

    contrast_fem_curve = dT_fem[:, 14, 20] - dT_fem[:, 4, 4]
    contrast_fdm_curve = dT_fdm[:, 14, 20] - dT_fdm[:, 4, 4]
    max_c_fem = float(np.max(contrast_fem_curve))
    max_c_fdm = float(np.max(contrast_fdm_curve))
    contrast_diff = abs(max_c_fdm - max_c_fem)

    frame_idx = int(0.8 * len(t_vec))
    spatial_fem = dT_fem[frame_idx].flatten()
    spatial_fdm = dT_fdm[frame_idx].flatten()
    r_spatial, _ = scipy.stats.pearsonr(spatial_fem, spatial_fdm)

    center_fem_t = dT_fem[:, 14, 20]
    center_fdm_t = dT_fdm[:, 14, 20]
    r_temporal, _ = scipy.stats.pearsonr(center_fem_t, center_fdm_t)

    return {
        "rel_l2_error_pct": float(rel_l2_pct),
        "peak_dT_fem_k": float(peak_fem),
        "peak_dT_fdm_k": float(peak_fdm),
        "peak_dT_diff_k": float(peak_diff),
        "peak_dT_diff_pct": float(peak_rel_err_pct),
        "peak_contrast_fem_k": float(max_c_fem),
        "peak_contrast_fdm_k": float(max_c_fdm),
        "contrast_diff_k": float(contrast_diff),
        "spatial_correlation": float(r_spatial),
        "temporal_correlation": float(r_temporal)
    }


def run_full_cross_validation():
    out_dir = Path("results/research_v3/matlab/cross_validation")
    out_dir.mkdir(parents=True, exist_ok=True)

    cases = [
        {"id": "healthy", "name": "Healthy Mild Steel Plate", "diameter_mm": 0.0, "depth_mm": 0.0},
        {"id": "slag_shallow", "name": "Shallow Slag Inclusion (d=0.4 mm)", "diameter_mm": 8.0, "depth_mm": 0.4},
        {"id": "slag_deep", "name": "Deep Slag Inclusion (d=0.8 mm)", "diameter_mm": 8.0, "depth_mm": 0.8}
    ]

    fem_backend = FEMBackend()
    matlab_backend = MATLABFDMBackend(mode="engine")
    analyzer = AutoDefectAnalyzer()

    results_summary = {}

    for case in cases:
        print(f"\n=================== Running Case: {case['name']} ===================")
        cfg = load_config("configs/research_v3_high_fidelity.yaml")
        cfg.geometry.inclusion.diameter_mm = case["diameter_mm"]
        cfg.geometry.inclusion.depth_mm = case["depth_mm"]
        cfg.geometry.inclusion.thickness_mm = 0.40 if case["diameter_mm"] > 0 else 0.0
        cfg.geometry.inclusion.center_x_mm = 50.0
        cfg.geometry.inclusion.center_y_mm = 35.0

        # Uniform simulation and camera parameters
        cfg.simulation.timestep_s = 0.04
        cfg.simulation.total_time_s = 10.0
        cfg.excitation.duration_s = 10.0
        cfg.camera.resolution_x = 40
        cfg.camera.resolution_y = 28
        cfg.camera.sampling_rate_hz = 10.0
        cfg.simulation.spatial_resolution["nx"] = 40
        cfg.simulation.spatial_resolution["ny"] = 28
        cfg.simulation.spatial_resolution["nz"] = 12


        # 1. Run Python FEM
        t0_fem = time.perf_counter()
        fem_res = fem_backend.run(cfg)
        time_fem = time.perf_counter() - t0_fem
        print(f"  [Python FEM] Completed in {time_fem:.2f} s. Peak dT: {np.max(fem_res.surface_temperature - 293.15):.3f} K, Frames: {len(fem_res.time_vector)}")

        # 2. Run MATLAB FDM
        t0_fdm = time.perf_counter()
        fdm_res = matlab_backend.run(cfg)
        time_fdm = time.perf_counter() - t0_fdm
        print(f"  [MATLAB FDM] Completed in {time_fdm:.2f} s. Peak dT: {np.max(fdm_res.surface_temperature - 293.15):.3f} K, Frames: {len(fdm_res.time_vector)}")

        # 3. Compute Metrics
        metrics = compute_cross_validation_metrics(
            fem_res.surface_temperature,
            fdm_res.surface_temperature,
            fem_res.time_vector,
            Tamb=cfg.excitation.ambient_temp_k
        )
        metrics["runtime_fem_s"] = float(time_fem)
        metrics["runtime_fdm_s"] = float(time_fdm)

        print(f"  --> Rel L2 Delta-T Error: {metrics['rel_l2_error_pct']:.2f} %")
        print(f"  --> Peak Delta-T Error:  {metrics['peak_dT_diff_k']:.3f} K ({metrics['peak_dT_diff_pct']:.2f} %)")
        print(f"  --> Contrast Diff:       {metrics['contrast_diff_k']:.3f} K")
        print(f"  --> Spatial Correlation:   {metrics['spatial_correlation']:.4f}")
        print(f"  --> Temporal Correlation:  {metrics['temporal_correlation']:.4f}")

        # 4. Pass MATLAB FDM thermograms through AutoDefectAnalyzer
        print(f"  [AutoDefectAnalyzer] Processing MATLAB thermograms...")
        ana_res = analyzer.analyze(
            source=fdm_res.surface_temperature,
            metadata_override={
                "source_type": "MATLAB_FDM",
                "frame_rate_hz": 10.0,
                "excitation_type": "LFMT_CHIRP"
            }
        )
        verdict = ana_res.consensus_verdict
        is_anom = verdict.get("is_anomaly_detected", False) if isinstance(verdict, dict) else getattr(verdict, "is_anomaly_detected", False)
        l_type = verdict.get("likely_defect_type", "UNKNOWN") if isinstance(verdict, dict) else getattr(verdict, "likely_defect_type", "UNKNOWN")
        conf = verdict.get("confidence", 0.0) if isinstance(verdict, dict) else getattr(verdict, "confidence", 0.0)
        print(f"  --> Verdict: Anomaly={is_anom}, Type={l_type}")

        results_summary[case["id"]] = {
            "case_info": case,
            "metrics": metrics,
            "analysis_verdict": {
                "is_anomaly_detected": is_anom,
                "likely_defect_type": l_type,
                "confidence": conf
            }
        }

    # Grid sensitivity study on MATLAB FDM (4 grid levels)
    print(f"\n=================== MATLAB FDM Grid Sensitivity Study ===================")
    grid_configs = [
        {"name": "coarse", "nx": 20, "ny": 14, "nz": 6},
        {"name": "baseline", "nx": 40, "ny": 28, "nz": 12},
        {"name": "medium", "nx": 60, "ny": 42, "nz": 18},
        {"name": "fine", "nx": 80, "ny": 56, "nz": 24}
    ]
    grid_results = {}
    grid_surfaces = {}

    for gc in grid_configs:
        cfg = load_config("configs/research_v3_high_fidelity.yaml")
        cfg.geometry.inclusion.diameter_mm = 8.0
        cfg.geometry.inclusion.depth_mm = 0.4
        cfg.geometry.inclusion.thickness_mm = 0.40
        cfg.simulation.timestep_s = 0.04
        cfg.simulation.total_time_s = 10.0
        cfg.excitation.duration_s = 10.0
        cfg.camera.resolution_x = 40
        cfg.camera.resolution_y = 28
        cfg.camera.sampling_rate_hz = 10.0
        cfg.simulation.spatial_resolution["nx"] = gc["nx"]
        cfg.simulation.spatial_resolution["ny"] = gc["ny"]
        cfg.simulation.spatial_resolution["nz"] = gc["nz"]
        
        t0 = time.perf_counter()
        res = matlab_backend.run(cfg)
        runtime = time.perf_counter() - t0

        dT = res.surface_temperature - 293.15
        peak_dt = float(np.max(dT))
        probe_dt = float(dT[int(0.8 * len(res.time_vector)), 14, 20])
        integrated_dt = float(np.sum(dT[int(0.8 * len(res.time_vector))]) * (100.0 * 70.0 * 1e-6 / (40 * 28)))

        grid_surfaces[gc["name"]] = dT
        grid_results[gc["name"]] = {
            "nx": gc["nx"], "ny": gc["ny"], "nz": gc["nz"],
            "total_cells": gc["nx"] * gc["ny"] * gc["nz"],
            "peak_dT_k": peak_dt,
            "probe_roi_dT_k": probe_dt,
            "integrated_surface_dT_k_m2": integrated_dt,
            "runtime_s": runtime
        }
        print(f"  [{gc['name']}] Cells={gc['nx']*gc['ny']*gc['nz']:5d}, Peak dT={peak_dt:.3f} K, Probe dT={probe_dt:.3f} K, Integrated dT={integrated_dt:.4f} K*m2, Runtime={runtime:.2f} s")

    # Compute relative L2 between successive grids
    names = ["coarse", "baseline", "medium", "fine"]
    for i in range(len(names) - 1):
        g1 = names[i]
        g2 = names[i + 1]
        diff_l2 = float(np.linalg.norm(grid_surfaces[g1] - grid_surfaces[g2]))
        ref_l2 = float(np.linalg.norm(grid_surfaces[g2]))
        rel_l2 = (diff_l2 / max(1e-12, ref_l2)) * 100.0
        grid_results[f"rel_l2_{g1}_vs_{g2}_pct"] = float(rel_l2)
        print(f"  --> Rel L2 Difference ({g1} vs {g2}): {rel_l2:.2f} %")

    results_summary["grid_sensitivity_study"] = grid_results

    # Temporal convergence study on MATLAB FDM
    print(f"\n=================== MATLAB FDM Temporal Convergence Study ===================")
    dt_configs = [0.08, 0.04, 0.02]
    dt_results = {}
    for dt_val in dt_configs:
        cfg = load_config("configs/research_v3_high_fidelity.yaml")
        cfg.geometry.inclusion.diameter_mm = 8.0
        cfg.geometry.inclusion.depth_mm = 0.4
        cfg.geometry.inclusion.thickness_mm = 0.40
        cfg.simulation.timestep_s = dt_val
        cfg.simulation.total_time_s = 10.0
        cfg.excitation.duration_s = 10.0
        cfg.camera.resolution_x = 40
        cfg.camera.resolution_y = 28
        cfg.camera.sampling_rate_hz = 10.0
        cfg.simulation.spatial_resolution["nx"] = 40
        cfg.simulation.spatial_resolution["ny"] = 28
        cfg.simulation.spatial_resolution["nz"] = 12


        t0 = time.perf_counter()
        res = matlab_backend.run(cfg)
        runtime = time.perf_counter() - t0
        peak_dt = float(np.max(res.surface_temperature - 293.15))
        dt_results[f"dt_{dt_val}s"] = {
            "dt_s": dt_val,
            "n_cam_frames": len(res.time_vector),
            "peak_dT_k": peak_dt,
            "runtime_s": runtime
        }
        print(f"  [dt={dt_val} s] Camera Frames={len(res.time_vector)}, Peak dT={peak_dt:.3f} K, Runtime={runtime:.2f} s")

    results_summary["temporal_convergence"] = dt_results

    # Save summary JSON
    summary_file = out_dir / "cross_validation_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)

    print(f"\nCross-validation study complete. Summary written to: {summary_file}")
    return results_summary


if __name__ == "__main__":
    run_full_cross_validation()

