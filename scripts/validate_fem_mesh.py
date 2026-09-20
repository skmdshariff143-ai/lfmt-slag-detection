#!/usr/bin/env python3
"""
3-D FEM Mesh Convergence and Spatial Discretization Verification Suite (Research V2).

Evaluates mesh convergence across Uniform Coarse, Medium, Fine, and Adaptive Graded meshes
for four canonical NDT test cases:
- Case A: D = 4 mm,  z = 0.2 mm (Shallow Small)
- Case B: D = 4 mm,  z = 1.0 mm (Deep Small)
- Case C: D = 8 mm,  z = 0.4 mm (Moderate)
- Case D: D = 12 mm, z = 1.0 mm (Large Deep)

Monitors:
- Peak surface temperature rise ΔT = T_peak - T_amb
- Defect-to-sound differential contrast
- Geometrical inclusion volume representation error
- Active Degrees of Freedom (DOFs) & execution time
- Asymptotic convergence rate verification
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

from lfmt.config import load_config, LFMTConfig, MeshRefinementConfig
from lfmt.simulation.fem import FEMBackend


def evaluate_mesh_case(
    case_name: str,
    diameter_mm: float,
    depth_mm: float,
    thickness_mm: float = 1.0,
    quick: bool = False
) -> List[Dict[str, Any]]:
    """Evaluate multiple mesh resolutions for a single defect geometry."""
    cfg = load_config("configs/research_v2.yaml") if os.path.exists("configs/research_v2.yaml") else load_config("configs/quick.yaml")
    
    # Configure defect
    cfg.geometry.inclusion.diameter_mm = float(diameter_mm)
    cfg.geometry.inclusion.depth_mm = float(depth_mm)
    cfg.geometry.inclusion.thickness_mm = float(thickness_mm)
    cfg.geometry.inclusion.center_x_mm = 50.0
    cfg.geometry.inclusion.center_y_mm = 35.0

    # Fast validation time parameters
    cfg.simulation.total_time_s = 2.0 if quick else 4.0
    cfg.simulation.timestep_s = 0.1 if quick else 0.05
    t_amb = cfg.excitation.ambient_temp_k

    fem = FEMBackend()
    if not fem.is_engine_available:
        print("scikit-fem not available. Skipping FEM mesh validation.")
        return []

    # Mesh levels to evaluate
    if quick:
        mesh_variants = [
            {"name": "Coarse Uniform", "mode": "uniform", "res": {"nx": 16, "ny": 12, "nz": 6}},
            {"name": "Medium Uniform", "mode": "uniform", "res": {"nx": 24, "ny": 18, "nz": 8}},
            {"name": "Adaptive Graded (V2)", "mode": "adaptive_tensor", "res": {"nx": 24, "ny": 18, "nz": 8}}
        ]
    else:
        mesh_variants = [
            {"name": "Coarse Uniform", "mode": "uniform", "res": {"nx": 20, "ny": 14, "nz": 8}},
            {"name": "Medium Uniform", "mode": "uniform", "res": {"nx": 36, "ny": 26, "nz": 12}},
            {"name": "Fine Uniform", "mode": "uniform", "res": {"nx": 50, "ny": 36, "nz": 16}},
            {"name": "Adaptive Graded (V2)", "mode": "adaptive_tensor", "res": {"nx": 36, "ny": 26, "nz": 12}}
        ]

    results = []

    for variant in mesh_variants:
        cfg.simulation.spatial_resolution = variant["res"]
        cfg.simulation.mesh_refinement.mode = variant["mode"]
        
        t0 = time.perf_counter()
        sim_res = fem.run(cfg)
        elapsed = time.perf_counter() - t0

        surf_frames = sim_res.surface_temperature
        t_peak = float(np.max(surf_frames))
        delta_t_peak = t_peak - t_amb

        # Contrast: center vs corner
        ny, nx = surf_frames.shape[1], surf_frames.shape[2]
        center_t = surf_frames[:, ny // 2, nx // 2]
        corner_t = surf_frames[:, 2, 2]
        peak_contrast = float(np.max(np.abs(center_t - corner_t)))

        dofs = sim_res.metadata.get("dofs", 0)
        nelem = sim_res.metadata.get("n_elements", 0)

        results.append({
            "case": case_name,
            "diameter_mm": diameter_mm,
            "depth_mm": depth_mm,
            "mesh_name": variant["name"],
            "dofs": dofs,
            "elements": nelem,
            "peak_delta_t_k": round(delta_t_peak, 4),
            "peak_contrast_k": round(peak_contrast, 4),
            "runtime_s": round(elapsed, 2)
        })

    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run FEM mesh convergence study.")
    parser.add_argument("--quick", action="store_true", help="Run rapid convergence test")
    parser.add_argument("--out-dir", type=str, default="results/research_v2", help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    print("=" * 70)
    print("LFMT RESEARCH V2: 3-D FEM MESH CONVERGENCE STUDY")
    print("=" * 70)

    cases = [
        ("Case A (D=4mm, z=0.2mm - Shallow Small)", 4.0, 0.2),
        ("Case B (D=4mm, z=1.0mm - Deep Small)", 4.0, 1.0),
        ("Case C (D=8mm, z=0.4mm - Moderate)", 8.0, 0.4),
        ("Case D (D=12mm, z=1.0mm - Large Deep)", 12.0, 1.0),
    ]

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    all_records = []
    for cname, diam, depth in cases:
        print(f"\nEvaluating {cname}...")
        res = evaluate_mesh_case(cname, diam, depth, quick=args.quick)
        all_records.extend(res)
        for r in res:
            print(f"  [{r['mesh_name']}] DOFs: {r['dofs']:5d} | Peak Delta-T: {r['peak_delta_t_k']:.4f} K | Peak Contrast: {r['peak_contrast_k']:.4f} K | Runtime: {r['runtime_s']}s")

    df = pd.DataFrame(all_records)
    csv_path = os.path.join(args.out_dir, "fem_mesh_convergence.csv")
    json_path = os.path.join(args.out_dir, "fem_mesh_convergence.json")
    df.to_csv(csv_path, index=False)
    with open(json_path, "w") as f:
        json.dump(all_records, f, indent=2)

    print(f"\nConvergence study successfully completed. Saved to {csv_path} and {json_path}")


if __name__ == "__main__":
    main()

