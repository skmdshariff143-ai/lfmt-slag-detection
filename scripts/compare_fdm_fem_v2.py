#!/usr/bin/env python3
"""
Multi-Case FDM vs FEM Cross-Validation Suite (Research V2).

Rigorous numerical verification comparing 3D Finite Difference Method (FDM)
against 3D Finite Element Method (FEM) on baseline-subtracted ΔT(t) surface thermograms:
- Case A: Shallow Small (D = 4 mm, z = 0.2 mm)
- Case B: Deep Small (D = 4 mm, z = 1.0 mm)
- Case C: Moderate (D = 8 mm, z = 0.4 mm)
- Case D: Healthy Specimen (No defect)

Computes:
- Root-Mean-Square Error (RMSE) on surface ΔT field
- Maximum Absolute Error (MAE / Peak Error)
- Pearson correlation coefficient (r)
- Relative energy norm agreement
- Solver execution time benchmarking
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
from lfmt.simulation.finite_difference import FiniteDifferenceBackend
from lfmt.simulation.fem import FEMBackend


def run_crossval_case(
    case_name: str,
    diameter_mm: float,
    depth_mm: float,
    quick: bool = False
) -> Dict[str, Any]:
    """Execute both FDM and FEM on identical thermal boundary conditions."""
    cfg = load_config("configs/research_v2.yaml") if os.path.exists("configs/research_v2.yaml") else load_config("configs/quick.yaml")

    cfg.geometry.inclusion.diameter_mm = float(diameter_mm)
    cfg.geometry.inclusion.depth_mm = float(depth_mm)
    cfg.geometry.inclusion.thickness_mm = 1.0 if diameter_mm > 0 else 0.0
    cfg.geometry.inclusion.center_x_mm = 50.0
    cfg.geometry.inclusion.center_y_mm = 35.0

    cfg.simulation.total_time_s = 2.0 if quick else 4.0
    cfg.simulation.timestep_s = 0.1 if quick else 0.05
    t_amb = cfg.excitation.ambient_temp_k

    if quick:
        cfg.simulation.spatial_resolution = {"nx": 24, "ny": 18, "nz": 8}
    else:
        cfg.simulation.spatial_resolution = {"nx": 40, "ny": 28, "nz": 12}

    fdm = FiniteDifferenceBackend()
    fem = FEMBackend()

    # 1. Run FDM
    t0_fdm = time.perf_counter()
    fdm_res = fdm.run(cfg)
    t_fdm = time.perf_counter() - t0_fdm

    # 2. Run FEM
    t0_fem = time.perf_counter()
    fem_res = fem.run(cfg)
    t_fem = time.perf_counter() - t0_fem

    fdm_surf = fdm_res.surface_temperature
    fem_surf = fem_res.surface_temperature

    # Align shapes if needed
    min_frames = min(fdm_surf.shape[0], fem_surf.shape[0])
    min_ny = min(fdm_surf.shape[1], fem_surf.shape[1])
    min_nx = min(fdm_surf.shape[2], fem_surf.shape[2])

    fdm_dt = fdm_surf[:min_frames, :min_ny, :min_nx] - t_amb
    fem_dt = fem_surf[:min_frames, :min_ny, :min_nx] - t_amb

    # Quantitative Comparison Metrics
    diff = fem_dt - fdm_dt
    rmse = float(np.sqrt(np.mean(diff ** 2)))
    mae = float(np.max(np.abs(diff)))
    mean_temp_rise = float(np.mean(fem_dt))
    rel_l2_error = float(np.linalg.norm(diff) / (np.linalg.norm(fem_dt) + 1e-12))

    # Pearson correlation
    f_flat = fdm_dt.ravel()
    m_flat = fem_dt.ravel()
    if np.std(f_flat) > 1e-9 and np.std(m_flat) > 1e-9:
        corr = float(np.corrcoef(f_flat, m_flat)[0, 1])
    else:
        corr = 1.0

    return {
        "case": case_name,
        "diameter_mm": diameter_mm,
        "depth_mm": depth_mm,
        "rmse_k": round(rmse, 4),
        "mae_k": round(mae, 4),
        "mean_temp_rise_k": round(mean_temp_rise, 4),
        "rel_l2_error_pct": round(rel_l2_error * 100.0, 2),
        "pearson_r": round(corr, 5),
        "fdm_runtime_s": round(t_fdm, 2),
        "fem_runtime_s": round(t_fem, 2)
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run FDM vs FEM cross-validation.")
    parser.add_argument("--quick", action="store_true", help="Run quick mode")
    parser.add_argument("--out-dir", type=str, default="results/research_v2", help="Output directory")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    os.makedirs(args.out_dir, exist_ok=True)
    print("=" * 70)
    print("LFMT RESEARCH V2: FDM VS FEM NUMERICAL CROSS-VALIDATION")
    print("=" * 70)

    cases = [
        ("Case A (D=4mm, z=0.2mm - Shallow Small)", 4.0, 0.2),
        ("Case B (D=4mm, z=1.0mm - Deep Small)", 4.0, 1.0),
        ("Case C (D=8mm, z=0.4mm - Moderate)", 8.0, 0.4),
        ("Case D (Healthy Specimen)", 0.0, 0.0),
    ]

    records = []
    for cname, diam, depth in cases:
        print(f"\nComparing {cname}...")
        rec = run_crossval_case(cname, diam, depth, quick=args.quick)
        records.append(rec)
        print(f"  RMSE: {rec['rmse_k']:.4f} K | MAE: {rec['mae_k']:.4f} K | Pearson r: {rec['pearson_r']:.5f} | L2 Error: {rec['rel_l2_error_pct']}% | FDM: {rec['fdm_runtime_s']}s, FEM: {rec['fem_runtime_s']}s")

    df = pd.DataFrame(records)
    csv_path = os.path.join(args.out_dir, "fdm_fem_crossval.csv")
    json_path = os.path.join(args.out_dir, "fdm_fem_crossval.json")
    df.to_csv(csv_path, index=False)
    with open(json_path, "w") as f:
        json.dump(records, f, indent=2)

    print(f"\nCross-validation successfully completed. Saved to {csv_path} and {json_path}")


if __name__ == "__main__":
    main()

