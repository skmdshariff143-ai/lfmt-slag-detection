#!/usr/bin/env python3
"""
Mesh Independence & Spatial Convergence Validation Suite.

Evaluates multi-resolution spatial convergence across Coarse, Medium, and Fine meshes:
1. Maximum surface temperature
2. Defect-region mean temperature
3. Sound-region mean temperature
4. Peak differential thermal contrast
5. Relative L2 spatial error relative to finest mesh
6. Defect localization error
Outputs results/validation/mesh_convergence.csv and results/validation/16_mesh_convergence.png
"""

import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from rich.console import Console
from rich.table import Table

from lfmt.config import load_config
from lfmt.simulation.finite_difference import FiniteDifferenceBackend
from lfmt.camera import VirtualIRCamera
from lfmt.detection import DefectDetector
from lfmt.contrast import RawThermalContrast


def main():
    parser = argparse.ArgumentParser(description="Validate spatial mesh independence.")
    parser.add_argument("--config", type=str, default="configs/quick.yaml", help="Config YAML")
    parser.add_argument("--out-dir", type=str, default="results/validation", help="Output directory")
    parser.add_argument("--quick", action="store_true", help="Quick mode for CI/rapid testing")
    args = parser.parse_args()

    console = Console()
    console.print("[bold cyan]LFMT Spatial Mesh Independence & Convergence Study[/bold cyan]")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.quick:
        mesh_levels = {
            "Coarse (20x14x8)": {"nx": 20, "ny": 14, "nz": 8},
            "Medium (40x28x16)": {"nx": 40, "ny": 28, "nz": 16},
            "Fine (60x42x24)": {"nx": 60, "ny": 42, "nz": 24},
        }
    else:
        mesh_levels = {
            "Coarse (30x21x10)": {"nx": 30, "ny": 21, "nz": 10},
            "Medium (60x42x20)": {"nx": 60, "ny": 42, "nz": 20},
            "Fine (90x63x30)": {"nx": 90, "ny": 63, "nz": 30},
        }

    backend = FiniteDifferenceBackend()
    camera_cfg = load_config(args.config).camera
    camera_cfg.resolution_x = 32
    camera_cfg.resolution_y = 32
    camera = VirtualIRCamera(camera_cfg)
    detector = DefectDetector(min_area_px=2)
    contrast_eval = RawThermalContrast()

    runs_data = []
    level_names = list(mesh_levels.keys())

    for label in level_names:
        res_dict = mesh_levels[label]
        console.print(f"Simulating mesh resolution: [yellow]{label}[/yellow]...")
        cfg = load_config(args.config)
        cfg.simulation.spatial_resolution = res_dict
        cfg.simulation.total_time_s = 3.0
        cfg.simulation.timestep_s = 0.1
        cfg.geometry.inclusion.diameter_mm = 8.0
        cfg.geometry.inclusion.depth_mm = 0.4

        sim_res = backend.run(cfg)
        capture = camera.capture(sim_res)

        t_vec = capture.time_vector
        t_celsius = capture.thermograms - 273.15  # (time, H, W)
        gt_mask = capture.ground_truth_mask
        sound_mask = ~gt_mask

        # Metrics
        max_temp_c = float(np.max(t_celsius))
        defect_mean_c = float(np.max(np.mean(t_celsius[:, gt_mask], axis=1)))
        sound_mean_c = float(np.max(np.mean(t_celsius[:, sound_mask], axis=1)))
        peak_contrast_k = defect_mean_c - sound_mean_c

        # Localization
        contrast_res = contrast_eval.process(capture.thermograms, t_vec, ground_truth_mask=gt_mask)
        det_res = detector.detect(contrast_res.contrast_map, fov_mm=(100.0, 70.0))
        gt_cx, gt_cy = cfg.geometry.inclusion.center_x_mm, cfg.geometry.inclusion.center_y_mm
        pred_cx, pred_cy = det_res.centroid_mm
        loc_err_mm = float(np.sqrt((pred_cx - gt_cx)**2 + (pred_cy - gt_cy)**2))

        # Center transient curve
        H, W = t_celsius.shape[1], t_celsius.shape[2]
        center_curve = t_celsius[:, H // 2, W // 2]

        runs_data.append({
            "label": label,
            "total_cells": res_dict["nx"] * res_dict["ny"] * res_dict["nz"],
            "max_temp_c": max_temp_c,
            "defect_mean_c": defect_mean_c,
            "sound_mean_c": sound_mean_c,
            "peak_contrast_k": peak_contrast_k,
            "loc_err_mm": loc_err_mm,
            "center_curve": center_curve,
            "time_vector": t_vec,
            "tensor": t_celsius,
            "runtime_s": sim_res.metadata["runtime_seconds"],
        })

    # Reference tensor is the finest mesh
    finest_tensor = runs_data[-1]["tensor"]
    summary_rows = []

    for item in runs_data:
        # L2 difference relative to finest mesh
        l2_diff = float(np.linalg.norm(item["tensor"] - finest_tensor))
        l2_ref = float(np.linalg.norm(finest_tensor))
        rel_l2_pct = (l2_diff / l2_ref) * 100.0 if l2_ref > 0 else 0.0

        summary_rows.append({
            "Mesh Resolution": item["label"],
            "Total Cells": item["total_cells"],
            "Max Temp [°C]": round(item["max_temp_c"], 3),
            "Defect Mean [°C]": round(item["defect_mean_c"], 3),
            "Sound Mean [°C]": round(item["sound_mean_c"], 3),
            "Peak Contrast [K]": round(item["peak_contrast_k"], 3),
            "Rel. L2 Error [%]": round(rel_l2_pct, 2),
            "Loc. Error [mm]": round(item["loc_err_mm"], 2),
            "Runtime [s]": round(item["runtime_s"], 2),
        })

    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(out_dir / "mesh_convergence.csv", index=False)

    # Print Table
    table = Table(title="Mesh Convergence & Spatial Independence Verification")
    table.add_column("Mesh Resolution", style="cyan")
    table.add_column("Total Cells", justify="right")
    table.add_column("Max Temp [°C]", justify="right")
    table.add_column("Defect [°C]", justify="right")
    table.add_column("Contrast [K]", justify="right")
    table.add_column("Rel. L2 Error", justify="right")
    table.add_column("Loc. Error [mm]", justify="right")
    table.add_column("Runtime [s]", justify="right")

    for r in summary_rows:
        table.add_row(
            r["Mesh Resolution"],
            str(r["Total Cells"]),
            f"{r['Max Temp [°C]']:.3f}",
            f"{r['Defect Mean [°C]']:.3f}",
            f"{r['Peak Contrast [K]']:.3f}",
            f"{r['Rel. L2 Error [%]']:.2f}%",
            f"{r['Loc. Error [mm]']:.2f}",
            f"{r['Runtime [s]']:.2f}s"
        )
    console.print(table)

    # Multi-panel Convergence Figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    colors = ["#e76f51", "#2a9d8f", "#264653"]

    for i, item in enumerate(runs_data):
        ax1.plot(item["time_vector"], item["center_curve"], lw=2.0, color=colors[i], label=item["label"])

    ax1.set_xlabel("Time [s]")
    ax1.set_ylabel("Defect Surface Temperature [°C]")
    ax1.set_title("Spatial Grid Independence (Center Temperature)")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend()

    # Subplot 2: Relative L2 Error vs Mesh Cells
    cells = [r["Total Cells"] for r in summary_rows]
    l2_errors = [r["Rel. L2 Error [%]"] for r in summary_rows]
    ax2.plot(cells, l2_errors, marker="o", lw=2.0, color="#7209b7")
    ax2.set_xlabel("Total Spatial Grid Cells")
    ax2.set_ylabel("Relative L2 Map Error [%] (vs Finest)")
    ax2.set_title("Spatial Discretization Convergence Rate")
    ax2.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    fig.savefig(out_dir / "16_mesh_convergence.png")
    fig.savefig(out_dir / "mesh_convergence.png")
    plt.close(fig)

    console.print(f"[bold green]Mesh convergence analysis complete! Saved to {out_dir}[/bold green]")


if __name__ == "__main__":
    main()
