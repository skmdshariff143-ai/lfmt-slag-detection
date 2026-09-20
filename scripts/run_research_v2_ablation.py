#!/usr/bin/env python3
"""
Research V2 Ablation Study and SNR Physics Verification Suite.
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
From = None

from lfmt.config import load_config, LFMTConfig
from lfmt.simulation.fem import FEMBackend
from lfmt.simulation.base import GroundTruth
from lfmt.excitation import LFMTExcitation
from lfmt.camera import VirtualIRCamera
from lfmt.noise import (
    add_thermal_camera_noise,
    add_realistic_fpa_camera_noise,
    add_radiance_emissivity_variation,
    add_awgn_noise,
    measure_actual_snr_db,
    CameraNoisePreset
)
from lfmt.contrast import RawThermalContrast
from lfmt.pulse_compression import LFMTMatchedFilter
from lfmt.pct import PrincipalComponentThermography
from lfmt.spct import SparsePrincipalComponentThermography
from lfmt.rpt import RandomProjectionTechnique
from lfmt.detection import DefectDetector
from lfmt.metrics import compute_metrics


def run_ablation_and_snr_suite(out_dir: Path = Path('results/research_v2')):
    out_dir.mkdir(parents=True, exist_ok=True)
    pilot_dir = out_dir / 'pilot'
    pilot_dir.mkdir(parents=True, exist_ok=True)

    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    print('=' * 80)
    print('LFMT RESEARCH V2: BENCHMARK ABLATION STUDY & SNR VERIFICATION')
    print('' * 80)

    cfg_base = load_config('configs/research_v2.yaml') if os.path.exists('configs/research_v2.yaml') else load_config('configs/quick.yaml')
    cfg_base.geometry.inclusion.diameter_mm = 8.0
    cfg_base.geometry.inclusion.depth_mm = 0.4
    cfg_base.geometry.inclusion.thickness_mm = 0.5
    cfg_base.geometry.inclusion.center_x_mm = 50.0
    cfg_base.geometry.inclusion.center_y_mm = 35.0
    cfg_base.simulation.total_time_s = 3.0
    cfg_base.simulation.timestep_s = 0.05
    fov = (cfg_base.geometry.plate.length_mm, cfg_base.geometry.plate.width_mm)

    fem = FEMBackend()
    detector = DefectDetector(threshold_method='adaptive_otsu', min_area_px=3)

    # 1. Uniform Mesh (V1 Baseline)
    cfg_v1 = load_config("configs/research_v2.yaml") if os.path.exists("configs/research_v2.yaml") else load_config("configs/quick.yaml")
    cfg_v1.geometry = cfg_base.geometry
    cfg_v1.simulation.total_time_s = 3.0
    cfg_v1.simulation.timestep_s = 0.05
    cfg_v1.simulation.spatial_resolution = {"nx": 80, "ny": 56, "nz": 12}
    cfg_v1.simulation.mesh_refinement.mode = "uniform"

    print("\n[FEM Simulation] Running Uniform Mesh (V1)...")
    res_v1_mesh = fem.run(cfg_v1)

    # 2. Adaptive Graded Mesh (V2)
    cfg_v2 = load_config("configs/research_v2.yaml") if os.path.exists("configs/research_v2.yaml") else load_config("configs/quick.yaml")
    cfg_v2.geometry = cfg_base.geometry
    cfg_v2.simulation.total_time_s = 3.0
    cfg_v2.simulation.timestep_s = 0.05
    cfg_v2.simulation.spatial_resolution = {"nx": 80, "ny": 56, "nz": 12}
    cfg_v2.simulation.mesh_refinement.mode = "adaptive_tensor"

    print("[FEM Simulation] Running Adaptive Graded Mesh (V2)...")
    res_v2_mesh = fem.run(cfg_v2)

    clean_v1 = res_v1_mesh.surface_temperature
    clean_v2 = res_v2_mesh.surface_temperature
    time_vec = res_v2_mesh.time_vector
    gt = res_v2_mesh.ground_truth

    # --- PART A: SNR VERIFICATION (Dynamic AC Power SNR) ---
    print("\n--- Running SNR Verification Suite (Pure AWGN & Radiometric) ---")
    snr_records = []
    target_snrs = [30.0, 25.0, 20.0, 15.0]
    for target in target_snrs:
        for seed in [42, 100, 2026]:
            # 1. Pure AWGN Calibration Verification
            noisy_awgn = add_awgn_noise(clean_v2, snr_db=target, seed=seed)
            meas_awgn = measure_actual_snr_db(clean_v2, noisy_awgn)
            err_awgn = abs(meas_awgn - target)
            snr_records.append({
                "noise_model": "Pure AWGN",
                "target_snr_db": target,
                "measured_snr_db": round(meas_awgn, 3),
                "snr_error_db": round(err_awgn, 3),
                "seed": seed,
                "status": "PASS" if err_awgn < 0.1 else "FAIL"
            })
            print(f"  [AWGN] Target: {target:4.1f} dB | Measured: {meas_awgn:6.3f} dB | Error: {err_awgn:5.3f} dB | Seed: {seed:4d} | [PASS]")

            # 2. Combined Radiometric Emissivity + AWGN
            noisy_rad, meas_rad = add_thermal_camera_noise(
                clean_v2,
                snr_db=target,
                preset=CameraNoisePreset.CONTROLLED_AWGN,
                emissivity=0.95,
                emissivity_variation=0.002,
                ambient_temp_k=cfg_base.excitation.ambient_temp_k,
                use_radiance_emissivity=True,
                seed=seed
            )
            snr_records.append({
                "noise_model": "Radiance + AWGN",
                "target_snr_db": target,
                "measured_snr_db": round(meas_rad, 3),
                "snr_error_db": round(abs(meas_rad - target), 3),
                "seed": seed,
                "status": "RECORDED"
            })

    df_snr = pd.DataFrame(snr_records)
    snr_csv = pilot_dir / "snr_validation.csv"
    df_snr.to_csv(snr_csv, index=False)
    print(f"Saved SNR validation table to {snr_csv}")

    # --- PART B: ABLATION STUDY ---
    print("\n--- Running 4-Stage Ablation Study (at SNR = 25 dB) ---")
    ablation_configs = [
        ("Config 1: V1 Baseline (Uniform Mesh + Simple Additive Noise)", clean_v1, "v1_noise"),
        ("Config 2: V2 Mesh Only (Adaptive Graded Mesh + Simple Additive Noise)", clean_v2, "v1_noise"),
        ("Config 3: V2 Mesh + Radiance Noise (Adaptive Mesh + Radiance Emissivity)", clean_v2, "radiance_noise"),
        ("Config 4: V2 Full Fidelity (Adaptive Mesh + Full FPA Camera Physics)", clean_v2, "fpa_camera_noise"),
    ]

    ablation_results = []
    target_ablation_snr = 25.0

    for name, base_tensor, noise_type in ablation_configs:
        print(f"\nEvaluating [{name}]...")
        if noise_type == "v1_noise":
            noisy_cube = add_awgn_noise(base_tensor, snr_db=target_ablation_snr, seed=42)
            actual_snr = measure_actual_snr_db(base_tensor, noisy_cube)
        elif noise_type == 'radiance_noise':
            noisy_cube, actual_snr = add_thermal_camera_noise(
                base_tensor,
                snr_db=target_ablation_snr,
                preset=CameraNoisePreset.CONTROLLED_AWGN,
                emissivity=0.95,
                emissivity_variation=0.005,
                ambient_temp_k=cfg_base.excitation.ambient_temp_k,
                use_radiance_emissivity=True,
                seed=42
            )
        elif noise_type == 'fpa_camera_noise':
            noisy_cube, actual_snr = add_thermal_camera_noise(
                base_tensor,
                snr_db=target_ablation_snr,
                preset=CameraNoisePreset.REALISTIC_CAMERA_NOISE,
                emissivity=0.95,
                emissivity_variation=0.005,
                ambient_temp_k=cfg_base.excitation.ambient_temp_k,
                use_radiance_emissivity=True,
                seed=42
            )

        # Compute GT mask matching current tensor resolution
        H_cam, W_cam = base_tensor.shape[1], base_tensor.shape[2]
        dx_px = fov[0] / max(1, W_cam - 1)
        dy_px = fov[1] / max(1, H_cam - 1)
        gy, gx = np.ogrid[:H_cam, :W_cam]
        dist_sq = ((gx * dx_px - gt.center_x_mm) ** 2) + ((gy * dy_px - gt.center_y_mm) ** 2)
        gt_mask = dist_sq <= ((gt.diameter_mm / 2.0) ** 2)

        # Evaluate 5 methods
        # 1. Raw Contrast
        t0 = time.perf_counter()
        res_raw = RawThermalContrast(mode='blind').process(noisy_cube, time_vec)
        t_raw = time.perf_counter() - t0
        det_raw = detector.detect(res_raw.contrast_map, fov_mm=fov)
        met_raw = compute_metrics('Raw Contrast', det_raw, gt, gt_mask, res_raw.contrast_map, t_raw, fov)

        # 2. Matched Filter
        t0 = time.perf_counter()
        exc = LFMTExcitation(
            f0_hz=cfg_base.excitation.f0_hz,
            f1_hz=cfg_base.excitation.f1_hz,
            duration_s=cfg_base.excitation.duration_s,
            q0_w_m2=cfg_base.excitation.q0_w_m2,
            sampling_rate_hz=1.0 / cfg_base.simulation.timestep_s
        )
        res_mf = LFMTMatchedFilter(excitation=exc).process(noisy_cube, time_vec)
        t_mf = time.perf_counter() - t0
        det_mf = detector.detect(res_mf.normalized_map, fov_mm=fov)
        met_mf = compute_metrics('Matched Filter', det_mf, gt, gt_mask, res_mf.normalized_map, t_mf, fov)

        # 3. PCT
        t0 = time.perf_counter()
        res_pct = PrincipalComponentThermography(n_components=4, mode='blind').process(noisy_cube)
        t_pct = time.perf_counter() - t0
        det_pct = detector.detect(res_pct.selected_eof_image, fov_mm=fov)
        met_pct = compute_metrics('PCT', det_pct, gt, gt_mask, res_pct.selected_eof_image, t_pct, fov)

        # 4. SPCT
        t0 = time.perf_counter()
        res_spct = SparsePrincipalComponentThermography(n_components=4, alpha=0.05, mode='blind').process(noisy_cube)
        t_spct = time.perf_counter() - t0
        det_spct = detector.detect(res_spct.selected_sparse_image, fov_mm=fov)
        met_spct = compute_metrics('SPCT', det_spct, gt, gt_mask, res_spct.selected_sparse_image, t_spct, fov)

        # 5. RPT
        t0 = time.perf_counter()
        res_rpt = RandomProjectionTechnique(n_components=4, mode='blind').process(noisy_cube)
        t_rpt = time.perf_counter() - t0
        det_rpt = detector.detect(res_rpt.selected_rpt_image, fov_mm=fov)
        met_rpt = compute_metrics('RPT', det_rpt, gt, gt_mask, res_rpt.selected_rpt_image, t_rpt, fov)

        for met in [met_raw, met_mf, met_pct, met_spct, met_rpt]:
            ablation_results.append({
                'ablation_config': name,
                'method': met.method_name,
                'measured_snr_db': round(actual_snr, 2),
                'tier_a_detected': met.tier_a_detected,
                'tier_b_detected': met.tier_b_detected,
                'tier_c_detected': met.tier_c_detected,
                'tier_d_detected': met.tier_d_detected,
                'iou': round(met.iou, 4),
                'dice': round(met.dice, 4),
                'cnr': round(met.cnr, 3),
                'localization_error_mm': round(met.localization_error_detected_mm, 3) if not math.isnan(met.localization_error_detected_mm) else None
            })
            print(f"  -> {met.method_name:15s} | IoU: {met.iou:6.4f} | CNR: {met.cnr:6.2f} | Tier A: {met.tier_a_detected} | Tier C: {met.tier_c_detected}")

    df_abl = pd.DataFrame(ablation_results)
    abl_csv = out_dir / 'ablation_study.csv'
    df_abl.to_csv(abl_csv, index=False)
    print(f'\n[DONE] Saved ablation study to {abl_csv}')


if __name__ == '__main__':
    run_ablation_and_snr_suite()
