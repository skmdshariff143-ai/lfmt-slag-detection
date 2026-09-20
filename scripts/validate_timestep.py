#!/usr/bin/env python3
"""
Time-Step Independence & Temporal Convergence Validation Suite.

Evaluates temporal numerical convergence across genuinely refined time steps (dt_1, dt_1/2, dt_1/4, dt_1/8)
using the implicit/explicit solvers:
- Records both requested dt and actual solver dt
- Measures peak front-surface temperature, defect center temperature, and defect contrast
- Evaluates spatial L2 map difference relative to the finest time step
- Computes convergence percentages
Outputs results/validation/timestep_convergence.csv and results/validation/17_timestep_convergence.png
"""

import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from rich.console import Console
from rich.table import Table

from lfmt.config import load_config
from lfmt.simulation.fem import FEMBackend
from lfmt.simulation.finite_difference import FiniteDifferenceBackend
from lfmt.camera import VirtualIRCamera


def main():
    parser = argparse.ArgumentParser(description="Validate time-step independence.")
    parser.add_argument("--config", type=str, default="configs/quick.yaml", help="Config YAML")
    parser.add_argument("--out-dir", type=str, default="results/validation", help="Output directory")
    parser.add_argument("--use-fem", action="store_true", help="Use implicit FEM solver for time-step study")
    parser.add_argument("--quick", action="store_true", help="Quick mode")
    args = parser.parse_args()

    console = Console()
    console.print("[bold cyan]LFMT Time-Step Independence & Temporal Convergence Study[/bold cyan]")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Systematic time step halving: dt_1, dt_1/2, dt_1/4, dt_1/8
    if args.quick:
        dt_values = [0.20, 0.10, 0.05]
    else:
        dt_values = [0.40, 0.20, 0.10, 0.05]

    # Select solver
    backend = FEMBackend() if (args.use_fem or FEMBackend().is_engine_available) else FiniteDifferenceBackend()
    console.print(f"Active Solver Backend: [yellow]{backend.backend_type.upper()}[/yellow]")

    camera_cfg = load_config(args.config).camera
    camera_cfg.resolution_x = 32
    camera_cfg.resolution_y = 32

    runs_data = []
    total_sim_time = 3.0

    for dt in dt_values:
        label = f"dt = {dt*1000:.0f} ms"
        console.print(f"Simulating time-step: [yellow]{label}[/yellow]...")
        cfg = load_config(args.config)
        cfg.simulation.spatial_resolution = {"nx": 24, "ny": 18, "nz": 8}
        cfg.simulation.total_time_s = total_sim_time
        cfg.simulation.timestep_s = dt
        cfg.geometry.inclusion.diameter_mm = 8.0
        cfg.geometry.inclusion.depth_mm = 0.4

        sim_res = backend.run(cfg)
        camera_cfg.sampling_rate_hz = 1.0 / dt
        camera = VirtualIRCamera(camera_cfg)
        capture = camera.capture(sim_res)

        t_vec = capture.time_vector
        t_celsius = capture.thermograms - 273.15  # (time, H, W)
        gt_mask = capture.ground_truth_mask
        sound_mask = ~gt_mask

        # Surface metrics
        peak_temp_c = float(np.max(t_celsius))
        final_temp_c = float(np.mean(t_celsius[-1]))
        
        # Defect center temperature
        H, W = t_celsius.shape[1], t_celsius.shape[2]
        center_curve = t_celsius[:, H // 2, W // 2]
        center_peak_c = float(np.max(center_curve))

        # Peak differential contrast
        defect_t = np.mean(t_celsius[:, gt_mask], axis=1)
        sound_t = np.mean(t_celsius[:, sound_mask], axis=1)
        peak_contrast_k = float(np.max(defect_t - sound_t))

        actual_dt_sub = sim_res.metadata.get("dt_sub_s", dt)

        runs_data.append({
            "label": label,
            "requested_dt_s": dt,
            "actual_dt_s": actual_dt_sub,
            "n_frames": len(t_vec),
            "peak_temp_c": peak_temp_c,
            "center_peak_c": center_peak_c,
            "final_temp_c": final_temp_c,
            "peak_contrast_k": peak_contrast_k,
            "time_vector": t_vec,
            "center_curve": center_curve,
            "final_map": t_celsius[-1],
            "runtime_s": sim_res.metadata["runtime_seconds"],
        })

    # Reference is the finest time step
    finest_final_map = runs_data[-1]["final_map"]
    finest_contrast = runs_data[-1]["peak_contrast_k"]
    summary_rows = []

    for item in runs_data:
        l2_diff = float(np.linalg.norm(item["final_map"] - finest_final_map))
        l2_ref = float(np.linalg.norm(finest_final_map))
        rel_l2_pct = (l2_diff / l2_ref) * 100.0 if l2_ref > 0 else 0.0

        contrast_dev_pct = abs(item["peak_contrast_k"] - finest_contrast) / (finest_contrast + 1e-6) * 100.0

        summary_rows.append({
            "Time Step": item["label"],
            "Requested dt [ms]": round(item["requested_dt_s"] * 1000, 1),
            "Actual dt [ms]": round(item["actual_dt_s"] * 1000, 3),
            "Frames": item["n_frames"],
            "Peak Temp [°C]": round(item["peak_temp_c"], 3),
            "Center Peak [°C]": round(item["center_peak_c"], 3),
            "Peak Contrast [K]": round(item["peak_contrast_k"], 3),
            "Final Map L2 Diff [%]": round(rel_l2_pct, 2),
            "Convergence [%]": round(100.0 - contrast_dev_pct, 2),
            "Runtime [s]": round(item["runtime_s"], 2),
        })

    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(out_dir / "timestep_convergence.csv", index=False)

    # Print Table
    table = Table(title="Time-Step Independence & Temporal Convergence Verification")
    table.add_column("Time Step", style="cyan")
    table.add_column("Req. dt", justify="right")
    table.add_column("Actual dt", justify="right")
    table.add_column("Frames", justify="right")
    table.add_column("Peak Temp [°C]", justify="right")
    table.add_column("Contrast [K]", justify="right")
    table.add_column("L2 Error", justify="right")
    table.add_column("Convergence", justify="right")
    table.add_column("Runtime", justify="right")

    for r in summary_rows:
        table.add_row(
            r["Time Step"],
            f"{r['Requested dt [ms]']:.0f}ms",
            f"{r['Actual dt [ms]']:.2f}ms",
            str(r["Frames"]),
            f"{r['Peak Temp [°C]']:.3f}",
            f"{r['Peak Contrast [K]']:.3f}",
            f"{r['Final Map L2 Diff [%]']:.2f}%",
            f"{r['Convergence [%]']:.1f}%",
            f"{r['Runtime [s]']:.2f}s"
        )
    console.print(table)

    # Multi-panel Convergence Figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    colors = ["#e76f51", "#2a9d8f", "#264653", "#9b5de5"]

    for i, item in enumerate(runs_data):
        ax1.plot(item["time_vector"], item["center_curve"], lw=2.0 - 0.2*i, color=colors[i % len(colors)], label=item["label"])

    ax1.set_xlabel("Time [s]")
    ax1.set_ylabel("Defect Surface Temperature [°C]")
    ax1.set_title("Temporal Convergence (Center Temperature)")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend()

    # Subplot 2: Relative Error vs dt
    dts = [r["Requested dt [ms]"] for r in summary_rows]
    l2_errors = [r["Final Map L2 Diff [%]"] for r in summary_rows]
    ax2.plot(dts, l2_errors, marker="s", lw=2.0, color="#d90429")
    ax2.set_xlabel("Time Step dt [ms]")
    ax2.set_ylabel("Relative L2 Map Error [%] (vs Finest dt)")
    ax2.set_title("Time-Step Discretization Error Rate")
    ax2.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    fig.savefig(out_dir / "17_timestep_convergence.png")
    fig.savefig(out_dir / "timestep_convergence.png")
    plt.close(fig)

    console.print(f"[bold green]Time-step convergence analysis complete! Saved to {out_dir}[/bold green]")


if __name__ == "__main__":
    main()
