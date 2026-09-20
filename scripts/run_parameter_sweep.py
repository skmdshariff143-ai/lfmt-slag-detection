#!/usr/bin/env python3
"""
Automated LFMT Parameter Sweep Script.

Executes a grid sweep over defect diameters, depths, and noise levels,
generating comprehensive CSV metrics tables and summary plots.
"""

import argparse
from pathlib import Path
from rich.console import Console

from lfmt.config import load_config
from lfmt.experiments import run_parameter_sweep
from lfmt.visualization import plot_depth_performance


def main():
    parser = argparse.ArgumentParser(description="Run LFMT parameter sweep.")
    parser.add_argument("--config", type=str, default="configs/quick.yaml", help="Base config YAML")
    parser.add_argument("--out-dir", type=str, default="results/sweep", help="Output directory")
    parser.add_argument("--quick", action="store_true", help="Quick mode (reduced grid for testing)")
    args = parser.parse_args()

    console = Console()
    console.print("[bold cyan]LFMT Automated Parameter Sweep Engine[/bold cyan]")

    base_cfg = load_config(args.config)

    if args.quick:
        diameters = [6.0, 10.0]
        depths = [0.4, 0.8]
        noises = [None, 25.0]
    else:
        diameters = [4.0, 6.0, 8.0, 10.0, 12.0]
        depths = [0.2, 0.4, 0.6, 0.8, 1.0]
        noises = [None, 30.0, 25.0, 20.0]

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"Sweeping Diameters: {diameters} mm")
    console.print(f"Sweeping Depths: {depths} mm")
    console.print(f"Sweeping Noise SNR: {noises} dB")

    sweep_df = run_parameter_sweep(
        base_config=base_cfg,
        diameters_mm=diameters,
        depths_mm=depths,
        noise_levels_db=noises,
        output_dir=out_dir
    )

    console.print(f"[bold green]Parameter sweep complete! Saved {len(sweep_df)} records to {out_dir / 'sweep_results.csv'}[/bold green]")

    # Generate depth performance plot
    fig = plot_depth_performance(sweep_df, save_path=out_dir / "depth_performance_curves.png")
    console.print(f"Depth curves saved to: [yellow]{out_dir / 'depth_performance_curves.png'}[/yellow]")


if __name__ == "__main__":
    main()
