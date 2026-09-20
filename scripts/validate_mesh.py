#!/usr/bin/env python3
"""
Mesh Independence & Spatial Convergence Validation Script.

Evaluates thermal surface transient and contrast convergence across
Coarse, Medium, and Fine spatial discretizations to verify mesh independence.
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


def main():
    parser = argparse.ArgumentParser(description="Validate spatial mesh independence.")
    parser.add_argument("--config", type=str, default="configs/quick.yaml", help="Config YAML")
    parser.add_argument("--out-dir", type=str, default="results/validation", help="Output directory")
    parser.add_argument("--quick", action="store_true", help="Faster grid sizes for CI/quick check")
    args = parser.parse_args()

    console = Console()
    console.print("[bold cyan]LFMT Spatial Mesh Independence Study[/bold cyan]")
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
            "Coarse (40x28x12)": {"nx": 40, "ny": 28, "nz": 12},
            "Medium (80x56x24)": {"nx": 80, "ny": 56, "nz": 24},
            "Fine (120x84x36)": {"nx": 120, "ny": 84, "nz": 36},
        }

    backend = FiniteDifferenceBackend()
    results = {}
    summary_rows = []

    for label, res_dict in mesh_levels.items():
        console.print(f"Simulating mesh level: [yellow]{label}[/yellow]...")
        cfg = load_config(args.config)
        cfg.simulation.spatial_resolution = res_dict

        sim_res = backend.run(cfg)
        surf = sim_res.surface_temperature  # (time, ny, nx)
        t = sim_res.time_vector

        # Sample center defect thermal history
        ny, nx = surf.shape[1], surf.shape[2]
        center_curve = surf[:, ny // 2, nx // 2]
        peak_t = float(np.max(center_curve)) - 273.15
        final_t = float(center_curve[-1]) - 273.15

        results[label] = (t, center_curve - 273.15)
        summary_rows.append({
            "Mesh Level": label,
            "Total Cells": res_dict["nx"] * res_dict["ny"] * res_dict["nz"],
            "Peak Temp [°C]": round(peak_t, 3),
            "Final Temp [°C]": round(final_t, 3),
            "Runtime [s]": round(sim_res.metadata["runtime_seconds"], 2)
        })

    # Summary table
    table = Table(title="Mesh Convergence Verification Table")
    table.add_column("Mesh Level", style="cyan")
    table.add_column("Total Cells", justify="right")
    table.add_column("Peak Temp [°C]", justify="right")
    table.add_column("Final Temp [°C]", justify="right")
    table.add_column("Runtime [s]", justify="right")

    for r in summary_rows:
        table.add_row(r["Mesh Level"], str(r["Total Cells"]), f"{r['Peak Temp [°C]']:.3f}", f"{r['Final Temp [°C]']:.3f}", f"{r['Runtime [s]']:.2f}")
    console.print(table)

    # Plot convergence
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#e76f51", "#2a9d8f", "#264653"]
    for i, (label, (t, curve)) in enumerate(results.items()):
        ax.plot(t, curve, lw=2.0, color=colors[i], label=label)

    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Defect Surface Temperature [°C]")
    ax.set_title("Mesh Independence & Spatial Convergence Analysis")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend()
    plt.tight_layout()

    fig_path = out_dir / "16_mesh_convergence.png"
    fig.savefig(fig_path)
    console.print(f"[bold green]Mesh convergence plot saved to: {fig_path}[/bold green]")


if __name__ == "__main__":
    main()
