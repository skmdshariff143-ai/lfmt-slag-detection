#!/usr/bin/env python3
"""
CLI entry point to execute an end-to-end LFMT simulation case and display metrics.
"""

import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table

from lfmt.config import load_config
from lfmt.excitation import LFMTExcitation
from lfmt.experiments import LFMTExperimentPipeline
from lfmt.visualization import (
    plot_excitation_waveform,
    plot_thermogram_progression,
    plot_temporal_contrast_curves,
    plot_method_comparison_panel,
    plot_runtime_comparison,
)


def main():
    parser = argparse.ArgumentParser(description="Run single LFMT simulation case.")
    parser.add_argument("--config", type=str, default="configs/quick.yaml", help="Path to config YAML")
    parser.add_argument("--diameter", type=float, default=None, help="Override defect diameter in mm")
    parser.add_argument("--depth", type=float, default=None, help="Override defect depth in mm")
    parser.add_argument("--noise", type=float, default=None, help="Override AWGN SNR in dB")
    parser.add_argument("--save-plots", action="store_true", help="Save publication figures to results/figures/")
    parser.add_argument("--out-dir", type=str, default="results", help="Output directory for metrics and figures")
    args = parser.parse_args()

    console = Console()
    console.print(f"[bold cyan]LFMT Slag Detection — Single Case Runner[/bold cyan]")
    console.print(f"Loading configuration from: [yellow]{args.config}[/yellow]")

    config = load_config(args.config)
    if args.diameter is not None:
        config.geometry.inclusion.diameter_mm = args.diameter
    if args.depth is not None:
        config.geometry.inclusion.depth_mm = args.depth
    if args.noise is not None:
        config.noise.snr_db = args.noise

    pipeline = LFMTExperimentPipeline()
    console.print("Running 3D transient thermal simulation and processing pipeline...")
    result = pipeline.run_case(config, use_cache=True)

    # Print summary table
    table = Table(title="LFMT Defect Characterization Performance Summary")
    table.add_column("Method", style="cyan", no_wrap=True)
    table.add_column("Detected?", style="bold")
    table.add_column("IoU", justify="right")
    table.add_column("Dice", justify="right")
    table.add_column("CNR", justify="right")
    table.add_column("Loc. Error [mm]", justify="right")
    table.add_column("Pred. Diam [mm]", justify="right")
    table.add_column("Runtime [ms]", justify="right")

    for row in result.metrics_dataframe.to_dict(orient="records"):
        detected_str = "[green]YES[/green]" if row["is_detected"] else "[red]NO[/red]"
        table.add_row(
            row["method_name"],
            detected_str,
            f"{row['iou']:.2f}",
            f"{row['dice']:.2f}",
            f"{row['cnr']:.1f}",
            f"{row['localization_error_mm']:.2f}",
            f"{row['predicted_diameter_mm']:.2f}",
            f"{row['runtime_s']*1000:.1f}"
        )

    console.print(table)
    console.print(f"[bold green]Case execution completed in {result.total_pipeline_time_s:.2f} s (Cache hit: {result.cache_hit})[/bold green]")

    if args.save_plots:
        fig_dir = Path(args.out_dir) / "figures"
        fig_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"Saving figures to [yellow]{fig_dir}[/yellow]...")

        exc = LFMTExcitation(
            f0_hz=config.excitation.f0_hz,
            f1_hz=config.excitation.f1_hz,
            duration_s=config.excitation.duration_s,
            q0_w_m2=config.excitation.q0_w_m2,
        )
        plot_excitation_waveform(exc, save_path=fig_dir / "01_lfmt_excitation.png")
        plot_thermogram_progression(result, save_path=fig_dir / "03_thermogram_progression.png")
        plot_temporal_contrast_curves(result, save_path=fig_dir / "04_contrast_curves.png")
        plot_method_comparison_panel(result, save_path=fig_dir / "05_method_comparison.png")
        plot_runtime_comparison(result.metrics_dataframe, save_path=fig_dir / "06_runtime_comparison.png")
        console.print(f"[bold green]Figures successfully saved to {fig_dir}![/bold green]")


if __name__ == "__main__":
    main()
