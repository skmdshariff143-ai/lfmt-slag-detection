#!/usr/bin/env python3
"""
FEM vs FDM Cross-Validation Benchmark Script.

Comprehensively compares the 3D Finite Element Method (scikit-fem) against
the 3D Finite Difference Method (FDM) across:
Case 1: Homogeneous mild steel plate
Case 2: Steel plate with centered subsurface slag inclusion

Evaluates:
- Mean surface temperature progression vs time
- Defect center temperature history
- Peak differential thermal contrast
- Relative L2 spatial map error and maximum absolute deviation (MAE)
- Generates CSV report and publication comparison figures.
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
from lfmt.simulation.fem import FEMBackend
from lfmt.camera import VirtualIRCamera


def main():
    parser = argparse.ArgumentParser(description="Cross-validate FEM vs FDM solvers.")
    parser.add_argument("--config", type=str, default="configs/quick.yaml", help="Base config YAML")
    parser.add_argument("--out-dir", type=str, default="results/validation", help="Output directory")
    args = parser.parse_args()

    console = Console()
    console.print("[bold cyan]LFMT FEM vs FDM Cross-Validation Suite[/bold cyan]")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    backend_fdm = FiniteDifferenceBackend()
    backend_fem = FEMBackend()

    if not backend_fem.is_engine_available:
        console.print("[bold red]FEM backend is not available! Cannot run comparison.[/bold red]")
        return

    # Use matching spatial and camera grids
    cfg_base = load_config(args.config)
    cfg_base.simulation.spatial_resolution = {"nx": 30, "ny": 22, "nz": 12}
    cfg_base.simulation.total_time_s = 4.0
    cfg_base.simulation.timestep_s = 0.1
    cfg_base.camera.resolution_x = 32
    cfg_base.camera.resolution_y = 32

    camera = VirtualIRCamera(cfg_base.camera)
    summary_records = []

    # =========================================================================
    # CASE 1: Homogeneous Steel Plate (No defect / material equality)
    # =========================================================================
    console.print("\n[bold yellow]CASE 1: Homogeneous Mild Steel Plate[/bold yellow]")
    cfg_c1 = load_config(args.config)
    cfg_c1.simulation.spatial_resolution = {"nx": 30, "ny": 22, "nz": 12}
    cfg_c1.simulation.total_time_s = 4.0
    cfg_c1.simulation.timestep_s = 0.1
    cfg_c1.camera.resolution_x = 32
    cfg_c1.camera.resolution_y = 32
    cfg_c1.geometry.inclusion.material = "mild_steel"

    res_fdm_c1 = backend_fdm.run(cfg_c1)
    res_fem_c1 = backend_fem.run(cfg_c1)

    cap_fdm_c1 = camera.capture(res_fdm_c1)
    cap_fem_c1 = camera.capture(res_fem_c1)

    t1 = cap_fdm_c1.time_vector
    t_fdm_c1 = cap_fdm_c1.thermograms - 273.15  # [°C]
    t_fem_c1 = cap_fem_c1.thermograms - 273.15  # [°C]

    mean_fdm_c1 = np.mean(t_fdm_c1, axis=(1, 2))
    mean_fem_c1 = np.mean(t_fem_c1, axis=(1, 2))
    peak_diff_c1 = np.max(np.abs(t_fdm_c1 - t_fem_c1))
    rel_l2_c1 = np.linalg.norm(t_fdm_c1 - t_fem_c1) / np.linalg.norm(t_fem_c1)

    summary_records.append({
        "Case": "Case 1: Homogeneous Steel Plate",
        "FDM Peak Temp [°C]": round(float(np.max(t_fdm_c1)), 3),
        "FEM Peak Temp [°C]": round(float(np.max(t_fem_c1)), 3),
        "Max Absolute Diff [K]": round(float(peak_diff_c1), 3),
        "Relative L2 Error [%]": round(float(rel_l2_c1 * 100), 2),
        "FDM Runtime [s]": round(res_fdm_c1.metadata["runtime_seconds"], 2),
        "FEM Runtime [s]": round(res_fem_c1.metadata["runtime_seconds"], 2),
    })

    # =========================================================================
    # CASE 2: Centered Subsurface Slag Inclusion
    # =========================================================================
    console.print("\n[bold yellow]CASE 2: Subsurface Slag Inclusion (D=8mm, z=0.4mm)[/bold yellow]")
    cfg_c2 = load_config(args.config)
    cfg_c2.simulation.spatial_resolution = {"nx": 30, "ny": 22, "nz": 12}
    cfg_c2.simulation.total_time_s = 4.0
    cfg_c2.simulation.timestep_s = 0.1
    cfg_c2.camera.resolution_x = 32
    cfg_c2.camera.resolution_y = 32
    cfg_c2.geometry.inclusion.diameter_mm = 8.0
    cfg_c2.geometry.inclusion.depth_mm = 0.4
    cfg_c2.geometry.inclusion.material = "slag"

    res_fdm_c2 = backend_fdm.run(cfg_c2)
    res_fem_c2 = backend_fem.run(cfg_c2)

    cap_fdm_c2 = camera.capture(res_fdm_c2)
    cap_fem_c2 = camera.capture(res_fem_c2)

    t_fdm_c2 = cap_fdm_c2.thermograms - 273.15
    t_fem_c2 = cap_fem_c2.thermograms - 273.15

    # Center defect temperature vs time
    H, W = t_fdm_c2.shape[1], t_fdm_c2.shape[2]
    center_fdm = t_fdm_c2[:, H // 2, W // 2]
    center_fem = t_fem_c2[:, H // 2, W // 2]

    # Sound reference
    sound_fdm = t_fdm_c2[:, 2, 2]
    sound_fem = t_fem_c2[:, 2, 2]

    contrast_fdm = center_fdm - sound_fdm
    contrast_fem = center_fem - sound_fem

    peak_diff_c2 = np.max(np.abs(t_fdm_c2 - t_fem_c2))
    rel_l2_c2 = np.linalg.norm(t_fdm_c2 - t_fem_c2) / np.linalg.norm(t_fem_c2)

    summary_records.append({
        "Case": "Case 2: Slag Inclusion (D=8mm, z=0.4mm)",
        "FDM Peak Temp [°C]": round(float(np.max(t_fdm_c2)), 3),
        "FEM Peak Temp [°C]": round(float(np.max(t_fem_c2)), 3),
        "Max Absolute Diff [K]": round(float(peak_diff_c2), 3),
        "Relative L2 Error [%]": round(float(rel_l2_c2 * 100), 2),
        "FDM Runtime [s]": round(res_fdm_c2.metadata["runtime_seconds"], 2),
        "FEM Runtime [s]": round(res_fem_c2.metadata["runtime_seconds"], 2),
    })

    # Output table
    df_summary = pd.DataFrame(summary_records)
    df_summary.to_csv(out_dir / "fdm_vs_fem.csv", index=False)

    table = Table(title="FEM vs FDM Cross-Validation Verification")
    table.add_column("Simulation Case", style="cyan")
    table.add_column("FDM Peak [°C]", justify="right")
    table.add_column("FEM Peak [°C]", justify="right")
    table.add_column("Max Abs Diff [K]", justify="right")
    table.add_column("Rel L2 Error", justify="right")
    table.add_column("FDM Time", justify="right")
    table.add_column("FEM Time", justify="right")

    for r in summary_records:
        table.add_row(
            r["Case"],
            f"{r['FDM Peak Temp [°C]']:.2f}",
            f"{r['FEM Peak Temp [°C]']:.2f}",
            f"{r['Max Absolute Diff [K]']:.3f}",
            f"{r['Relative L2 Error [%]']:.2f}%",
            f"{r['FDM Runtime [s]']:.2f}s",
            f"{r['FEM Runtime [s]']:.2f}s"
        )
    console.print(table)

    # =========================================================================
    # PLOTS
    # =========================================================================
    console.print("Generating cross-validation figures...")

    # Figure 1: Surface Mean and Center Temperature vs Time
    fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    ax1.plot(t1, mean_fdm_c1, "r-", lw=2, label="FDM (Case 1)")
    ax1.plot(t1, mean_fem_c1, "b--", lw=2, label="FEM (Case 1)")
    ax1.set_xlabel("Time [s]")
    ax1.set_ylabel("Surface Mean Temp [°C]")
    ax1.set_title("Case 1: Homogeneous Plate Thermal Response")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend()

    ax2.plot(t1, center_fdm, "r-", lw=2, label="FDM Defect Center")
    ax2.plot(t1, center_fem, "b--", lw=2, label="FEM Defect Center")
    ax2.plot(t1, sound_fdm, "r:", lw=1.5, label="FDM Sound")
    ax2.plot(t1, sound_fem, "b:", lw=1.5, label="FEM Sound")
    ax2.set_xlabel("Time [s]")
    ax2.set_ylabel("Surface Temp [°C]")
    ax2.set_title("Case 2: Slag Inclusion Thermal Response")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend()
    plt.tight_layout()
    fig1.savefig(out_dir / "fdm_vs_fem_temperature.png")
    plt.close(fig1)

    # Figure 2: Defect Thermal Contrast vs Time
    fig2, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(t1, contrast_fdm, "r-", lw=2.2, label="FDM Differential Contrast")
    ax.plot(t1, contrast_fem, "b--", lw=2.2, label="FEM Differential Contrast")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Differential Contrast Delta T [K]")
    ax.set_title("Differential Thermal Contrast Comparison (FDM vs FEM)")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend()
    plt.tight_layout()
    fig2.savefig(out_dir / "fdm_vs_fem_contrast.png")
    plt.close(fig2)

    # Figure 3: Spatial Map Difference
    peak_frame = int(np.argmax(contrast_fem))
    fig3, axes = plt.subplots(1, 3, figsize=(13, 4))
    im1 = axes[0].imshow(t_fdm_c2[peak_frame], origin="lower", cmap="inferno")
    axes[0].set_title(f"FDM Thermal Map (t={t1[peak_frame]:.1f}s)")
    fig3.colorbar(im1, ax=axes[0], label="Temp [°C]")

    im2 = axes[1].imshow(t_fem_c2[peak_frame], origin="lower", cmap="inferno")
    axes[1].set_title(f"FEM Thermal Map (t={t1[peak_frame]:.1f}s)")
    fig3.colorbar(im2, ax=axes[1], label="Temp [°C]")

    diff_map = t_fdm_c2[peak_frame] - t_fem_c2[peak_frame]
    im3 = axes[2].imshow(diff_map, origin="lower", cmap="bwr")
    axes[2].set_title(f"Difference Map (FDM - FEM)\nMax Diff = {np.max(np.abs(diff_map)):.3f} K")
    fig3.colorbar(im3, ax=axes[2], label="Temp Diff [K]")

    for a in axes:
        a.set_xlabel("X [px]")
        a.set_ylabel("Y [px]")

    plt.tight_layout()
    fig3.savefig(out_dir / "fdm_vs_fem_map_difference.png")
    plt.close(fig3)

    console.print(f"[bold green]FEM vs FDM comparison successfully completed! Saved to {out_dir}[/bold green]")


if __name__ == "__main__":
    main()
