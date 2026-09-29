#!/usr/bin/env python3
"""
Research V2 Pilot Study Runner & Computational Benchmark Estimator.

Runs a focused, high-fidelity pilot study across:
- 4 Geometries: D=4mm z=0.2mm, D=8mm z=0.4mm, D=12mm z=1.0mm, and Healthy Specimen (0mm)
- 2 Noise Levels: Clean (None) and 30 dB SNR (Controlled AWGN + Radiance Emissivity)
- 5 Methods: Raw Contrast, Matched Filter, PCT, SPCT, RPT
- Multi-tier evaluation: Tiers A, B, C, D

Measures exact FEM solver runtime, processing runtime, and projects full 4,030-evaluation compute cost.
Outputs saved to results/research_v2/pilot/
"""

from __future__ import annotations
import os
import sys
import json
import time
import math
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import pandas as pd

from lfmt.config import load_config, LFMTConfig
from lfmt.simulation.fem import FEMBackend
from lfmt.simulation.base import GroundTruth
from lfmt.excitation import LFMTExcitation
from lfmt.camera import VirtualIRCamera
from lfmt.noise import add_thermal_camera_noise, CameraNoisePreset
from lfmt.contrast import RawThermalContrast
from lfmt.pulse_compression import LFMTMatchedFilter
from lfmt.pct import PrincipalComponentThermography
from lfmt.spct import SparsePrincipalComponentThermography
from lfmt.rpt import RandomProjectionTechnique
from lfmt.detection import DefectDetector
from lfmt.metrics import compute_metrics


def run_pilot():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    out_dir = Path("results/research_v2/pilot")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("LFMT RESEARCH V2: HIGH-FIDELITY PILOT STUDY")
    print("=" * 70)

    # 1. Pilot configurations
    cases = [
        {"case_id": "D4_z0.2", "name": "Shallow Small (D=4mm, z=0.2mm)", "diameter": 4.0, "depth": 0.2, "thick": 1.0},
        {"case_id": "D8_z0.4", "name": "Moderate (D=8mm, z=0.4mm)", "diameter": 8.0, "depth": 0.4, "thick": 1.0},
        {"case_id": "D12_z1.0", "name": "Large Deep (D=12mm, z=1.0mm)", "diameter": 12.0, "depth": 1.0, "thick": 1.0},
        {"case_id": "Healthy", "name": "Healthy Control (D=0mm, z=0.0mm)", "diameter": 0.0, "depth": 0.0, "thick": 0.0}
    ]

    noise_levels = [
        {"noise_id": "Clean", "snr_db": None, "emissivity_var": 0.0},
        {"noise_id": "SNR_30dB", "snr_db": 30.0, "emissivity_var": 0.005}
    ]

    cfg = load_config("configs/research_v2.yaml") if os.path.exists("configs/research_v2.yaml") else load_config("configs/quick.yaml")
    cfg.simulation.total_time_s = 4.0
    cfg.simulation.timestep_s = 0.05
    cfg.simulation.spatial_resolution = {"nx": 32, "ny": 24, "nz": 10}
    cfg.simulation.mesh_refinement.mode = "adaptive_tensor"

    fem = FEMBackend()
    camera = VirtualIRCamera(cfg.camera)
    detector = DefectDetector(threshold_method="adaptive_otsu", min_area_px=3)

    all_results = []
    fem_runtimes = []
    proc_runtimes = []

    print("\n--- Running Pilot Simulations & Algorithms ---")
    start_all = time.perf_counter()

    for c in cases:
        cfg.geometry.inclusion.diameter_mm = c["diameter"]
        cfg.geometry.inclusion.depth_mm = c["depth"]
        cfg.geometry.inclusion.thickness_mm = c["thick"]
        cfg.geometry.inclusion.center_x_mm = 50.0
        cfg.geometry.inclusion.center_y_mm = 35.0

        print(f"\n[FEM Simulation] Running {c['name']}...")
        t0_fem = time.perf_counter()
        sim_res = fem.run(cfg)
        t_fem = time.perf_counter() - t0_fem
        fem_runtimes.append(t_fem)
        print(f"  FEM Completed in {t_fem:.2f}s (DOFs: {sim_res.metadata.get('dofs', 'N/A')})")

        clean_surf = sim_res.surface_temperature
        time_vec = sim_res.time_vector
        gt = sim_res.ground_truth

        # Ground truth 2D mask on camera grid
        H_cam, W_cam = clean_surf.shape[1], clean_surf.shape[2]
        gt_mask = np.zeros((H_cam, W_cam), dtype=bool)
        if gt.has_defect:
            dx_px = 100.0 / max(1, W_cam - 1)
            dy_px = 70.0 / max(1, H_cam - 1)
            gy, gx = np.ogrid[:H_cam, :W_cam]
            dist_sq = ((gx * dx_px - gt.center_x_mm) ** 2) + ((gy * dy_px - gt.center_y_mm) ** 2)
            gt_mask = dist_sq <= ((gt.diameter_mm / 2.0) ** 2)

        for nl in noise_levels:
            if nl["snr_db"] is not None:
                noisy_surf, actual_snr = add_thermal_camera_noise(
                    clean_surf,
                    snr_db=nl["snr_db"],
                    preset=CameraNoisePreset.CONTROLLED_AWGN,
                    emissivity=0.95,
                    emissivity_variation=nl["emissivity_var"],
                    ambient_temp_k=cfg.excitation.ambient_temp_k,
                    use_radiance_emissivity=True,
                    seed=42
                )
            else:
                noisy_surf = clean_surf.copy()
                actual_snr = float("inf")

            fov = (cfg.geometry.plate.length_mm, cfg.geometry.plate.width_mm)

            # 1. Raw Contrast
            t0_raw = time.perf_counter()
            raw_eng = RawThermalContrast(mode="blind")
            res_raw = raw_eng.process(noisy_surf, time_vec)
            t_raw = time.perf_counter() - t0_raw
            proc_runtimes.append(t_raw)
            det_raw = detector.detect(res_raw.contrast_map, fov_mm=fov)
            met_raw = compute_metrics("Raw Contrast", det_raw, gt, gt_mask, res_raw.contrast_map, t_raw, fov)

            # 2. Matched Filter
            t0_mf = time.perf_counter()
            exc = LFMTExcitation(
                f0_hz=cfg.excitation.f0_hz,
                f1_hz=cfg.excitation.f1_hz,
                duration_s=cfg.excitation.duration_s,
                q0_w_m2=cfg.excitation.q0_w_m2,
                sampling_rate_hz=cfg.camera.sampling_rate_hz
            )
            mf_eng = LFMTMatchedFilter(excitation=exc)
            res_mf = mf_eng.process(noisy_surf, time_vec)
            t_mf = time.perf_counter() - t0_mf
            proc_runtimes.append(t_mf)
            det_mf = detector.detect(res_mf.normalized_map, fov_mm=fov)
            met_mf = compute_metrics("Matched Filter", det_mf, gt, gt_mask, res_mf.normalized_map, t_mf, fov)

            # 3. PCT
            t0_pct = time.perf_counter()
            pct_eng = PrincipalComponentThermography(n_components=4, mode="blind")
            res_pct = pct_eng.process(noisy_surf)
            t_pct = time.perf_counter() - t0_pct
            proc_runtimes.append(t_pct)
            det_pct = detector.detect(res_pct.selected_eof_image, fov_mm=fov)
            met_pct = compute_metrics("PCT", det_pct, gt, gt_mask, res_pct.selected_eof_image, t_pct, fov)

            # 4. SPCT
            t0_spct = time.perf_counter()
            spct_eng = SparsePrincipalComponentThermography(n_components=4, alpha=0.05, max_iter=30, tol=1e-2, mode="blind")
            res_spct = spct_eng.process(noisy_surf)
            t_spct = time.perf_counter() - t0_spct
            proc_runtimes.append(t_spct)
            det_spct = detector.detect(res_spct.selected_sparse_image, fov_mm=fov)
            met_spct = compute_metrics("SPCT", det_spct, gt, gt_mask, res_spct.selected_sparse_image, t_spct, fov)

            # 5. RPT
            t0_rpt = time.perf_counter()
            rpt_eng = RandomProjectionTechnique(n_components=4, matrix_type="gaussian", mode="blind")
            res_rpt = rpt_eng.process(noisy_surf)
            t_rpt = time.perf_counter() - t0_rpt
            proc_runtimes.append(t_rpt)
            det_rpt = detector.detect(res_rpt.selected_rpt_image, fov_mm=fov)
            met_rpt = compute_metrics("RPT", det_rpt, gt, gt_mask, res_rpt.selected_rpt_image, t_rpt, fov)

            for met in [met_raw, met_mf, met_pct, met_spct, met_rpt]:
                rec = {
                    "case_id": c["case_id"],
                    "case_name": c["name"],
                    "diameter_mm": c["diameter"],
                    "depth_mm": c["depth"],
                    "noise_level": nl["noise_id"],
                    "target_snr_db": nl["snr_db"],
                    "actual_snr_db": round(actual_snr, 2) if not math.isinf(actual_snr) else "inf",
                    "method": met.method_name,
                    "tier_a_detected": met.tier_a_detected,
                    "tier_b_detected": met.tier_b_detected,
                    "tier_c_detected": met.tier_c_detected,
                    "tier_d_detected": met.tier_d_detected,
                    "is_false_positive": met.is_false_positive,
                    "iou": round(met.iou, 4),
                    "dice": round(met.dice, 4),
                    "cnr": round(met.cnr, 3),
                    "localization_error_mm": round(met.localization_error_detected_mm, 3) if not math.isnan(met.localization_error_detected_mm) else None,
                    "roc_auc": round(met.roc_auc, 4) if met.roc_auc is not None else None,
                    "processing_time_s": round(met.runtime_seconds, 4)
                }
                all_results.append(rec)

    total_pilot_time = time.perf_counter() - start_all

    df = pd.DataFrame(all_results)
    csv_path = out_dir / "pilot_study_results.csv"
    json_path = out_dir / "pilot_study_results.json"
    df.to_csv(csv_path, index=False)
    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2)

    # 2. Benchmark Projection Calculations
    avg_fem_s = float(np.mean(fem_runtimes))
    avg_proc_s = float(np.mean(proc_runtimes))
    
    # Full V2 Study Size: 26 geometries (25 defects + 1 healthy) x 4 noise levels (Clean, 30dB, 25dB, 20dB) x 10 seeds x 5 methods
    # Number of distinct FEM simulations = 26 geometries (noise applied post-simulation)
    # Number of method evaluations = 26 x (1 + 3 x 10) x 5 = 26 x 31 x 5 = 4,030 evaluations
    total_fem_sims = 26
    total_evals = 4030

    projected_fem_hours = (total_fem_sims * avg_fem_s) / 3600.0
    projected_proc_hours = (total_evals * avg_proc_s) / 3600.0
    total_projected_hours = projected_fem_hours + projected_proc_hours

    projection_summary = {
        "pilot_cases_count": len(cases),
        "pilot_total_evaluations": len(all_results),
        "pilot_total_runtime_s": round(total_pilot_time, 2),
        "avg_fem_simulation_time_s": round(avg_fem_s, 2),
        "avg_method_processing_time_s": round(avg_proc_s, 4),
        "full_benchmark_fem_simulations_needed": total_fem_sims,
        "full_benchmark_evaluations_total": total_evals,
        "projected_fem_time_hours": round(projected_fem_hours, 3),
        "projected_processing_time_hours": round(projected_proc_hours, 3),
        "total_projected_benchmark_time_hours": round(total_projected_hours, 3),
        "total_projected_benchmark_time_minutes": round(total_projected_hours * 60.0, 1)
    }

    proj_path = out_dir / "computational_cost_projection.json"
    with open(proj_path, "w") as f:
        json.dump(projection_summary, f, indent=2)

    print("\n" + "=" * 70)
    print("PILOT STUDY RESULTS SUMMARY")
    print("=" * 70)
    print(f"Total Evaluations Executed: {len(all_results)}")
    print(f"Total Pilot Runtime: {total_pilot_time:.2f}s")
    print(f"Average FEM Solve Time: {avg_fem_s:.2f}s per case")
    print(f"Average Algorithm Processing Time: {avg_proc_s*1000.0:.2f}ms per evaluation")
    print(f"Projected Full 4,030 V2 Benchmark Time: {total_projected_hours:.3f} hours ({total_projected_hours*60.0:.1f} minutes)")
    print(f"Results saved to: {csv_path}")
    print("=" * 70)


if __name__ == "__main__":
    run_pilot()

