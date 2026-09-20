#!/usr/bin/env python3
"""
Time-Step Independence & Temporal Convergence Validation Script.

Evaluates thermal transient response stability and numerical convergence
as output and sub-stepping time step sizes dt are systematically refined.
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
    parser = argparse.ArgumentParser(description="Validate time-step independence.")
    parser.add_argument("--config", type=str, default="configs/quick.yaml", help="Config YAML")
    parser.add_argument("--out-dir", type=str, default="results/validation", help="Output directory")
    parser.add_argument("--quick", action="store_true", help="Quick mode")
    args = parser.parse_args()

    console = Console()
    console.print("[bold cyan]LFMT Time-Step Independence Study[/bold cyan]")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.quick:
        dt_values = [0.20, 0.10, 0.05]
    else:
        dt_values = [0.10, 0.05, 0.02, 0.01]

    backend = FiniteDifferenceBackend()
    results = {}
    summary_rows = []

    for dt in dt_values:
        label = f"dt = {dt*1000:.0f} ms"
        console.print(f"Simulating time-step: [yellow]{label}[/yellow]...")
        cfg = load_config(args.config)
        cfg.simulation.timestep_s = dt

        sim_res = backend.run(cfg)
        surf = sim_res.surface_temperature
        t = sim_res.time_vector

        ny, nx = surf.shape[1], surf.shape[2]
        center_curve = surf[:, ny // 2, nx // 2]
        peak_t = float(np.max(center_curve)) - 273.15
        final_t = float(center_curve[-1]) - 273.15

        results[label] = (t, center_curve - 273.15)
        summary_rows.append({
            "Time Step": label,
            "dt [s]": dt,
            "Frames": len(t),
            "Peak Temp [°C]": round(peak_t, 3),
            "Final Temp [°C]": round(final_t, 3),
            "Runtime [s]": round(sim_res.metadata["runtime_seconds"], 2)
        })

    # Summary table
    table = Table(title="Time-Step Convergence Verification Table")
    table.add_column("Time Step", style="cyan")
    table.add_column("Frames", justify="right")
    table.add_column("Peak Temp [°C]", justify="right")
    table.add_column("Final Temp [°C]", justify="right")
    table.add_column("Runtime [s]", justify="right")

    for r in summary_rows:
        table.add_row(r["Time Step"], str(r["Frames"]), f"{r['Peak Temp [°C]']:.3f}", f"{r['Final Temp [°C]']:.3f}", f"{r['Runtime [s]']:.2f}")
    console.print(table)

    # Plot convergence
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#e76f51", "#2a9d8f", "#264653", "#9b5de5"]
    for i, (label, (t, curve)) in enumerate(results.items()):
        ax.plot(t, curve, lw=2.0 - 0.3*i, linestyle="-" if i==0 else "--", color=colors[i % len(colors)], label=label)

    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Defect Surface Temperature [°C]")
    ax.set_title("Time-Step Independence & Temporal Convergence Analysis")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend()
    plt.tight_layout()

    fig_path = out_dir / "17_timestep_convergence.png"
    fig.savefig(fig_path)
    console.print(f"[bold green]Time-step convergence plot saved to: {fig_path}[/bold green]")


if __name__ == "__main__":
    main()
