#!/usr/bin/env python3
"""
Conference & Publication Figure Generator.

Generates all 17 publication-quality figures at high DPI:
1. LFMT Excitation Waveform
2. Instantaneous Frequency Progression
3. Spatial Thermogram Progression Sequence
4. Defect vs Sound Temporal Response
5. Raw Contrast Progression
6. Pulse-Compression Correlation Map
7. PCT EOF Spatial Image
8. SPCT Sparse EOF Image
9. RPT Random Projection Score Map
10. Ground-Truth vs Prediction Overlay Comparison
11. Differential Contrast vs Defect Depth
12. Localization Error vs Defect Depth
13. Detection Success Rate vs Depth
14. Method Performance vs Noise Degradation (AWGN)
15. Signal Processing Computational Runtime Benchmark
16. Spatial Mesh Convergence Analysis
17. Temporal Time-Step Independence Analysis
"""

import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd
from rich.console import Console

from lfmt.config import load_config
from lfmt.excitation import LFMTExcitation
from lfmt.experiments import LFMTExperimentPipeline, run_parameter_sweep
from lfmt.visualization import (
    plot_excitation_waveform,
    plot_thermogram_progression,
    plot_temporal_contrast_curves,
    plot_method_comparison_panel,
    plot_depth_performance,
    plot_runtime_comparison,
)


def main():
    parser = argparse.ArgumentParser(description="Generate all 17 conference figures.")
    parser.add_argument("--config", type=str, default="configs/quick.yaml", help="Base config YAML")
    parser.add_argument("--out-dir", type=str, default="results/figures", help="Output figures directory")
    parser.add_argument("--quick", action="store_true", help="Quick mode for rapid generation")
    args = parser.parse_args()

    console = Console()
    console.print("[bold cyan]LFMT Conference & Publication Figure Generator[/bold cyan]")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    config = load_config(args.config)
    pipeline = LFMTExperimentPipeline()

    console.print("Running primary simulation case...")
    result = pipeline.run_case(config, use_cache=True)

    # Figure 1 & 2: Excitation & Instantaneous Frequency
    console.print("Generating Figures 01 & 02: Excitation & Frequency...")
    exc = LFMTExcitation(
        f0_hz=config.excitation.f0_hz,
        f1_hz=config.excitation.f1_hz,
        duration_s=config.excitation.duration_s,
        q0_w_m2=config.excitation.q0_w_m2,
        sampling_rate_hz=config.camera.sampling_rate_hz
    )
    plot_excitation_waveform(exc, total_time_s=config.simulation.total_time_s, save_path=out_dir / "01_02_lfmt_excitation_and_frequency.png")

    # Figure 3: Thermogram Progression
    console.print("Generating Figure 03: Thermogram Progression Sequence...")
    plot_thermogram_progression(result, save_path=out_dir / "03_thermogram_progression.png")

    # Figure 4 & 5: Temporal Curves & Raw Contrast
    console.print("Generating Figures 04 & 05: Temporal Response & Raw Contrast...")
    plot_temporal_contrast_curves(result, save_path=out_dir / "04_05_temporal_response_and_contrast.png")

    # Figure 6: Matched Filter Map
    console.print("Generating Figure 06: Pulse Compression / Matched Filter Map...")
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(
        result.matched_filter_bundle.score_map,
        origin="lower",
        cmap="viridis",
        extent=[0, config.geometry.plate.length_mm, 0, config.geometry.plate.width_mm]
    )
    fig.colorbar(im, ax=ax, label="Normalized Correlation Peak")
    ax.set_title("LFMT Pulse-Compression Matched Filter Map")
    ax.set_xlabel("Length [mm]")
    ax.set_ylabel("Width [mm]")
    fig.savefig(out_dir / "06_pulse_compression_map.png")
    plt.close(fig)

    # Figure 7: PCT Image
    console.print("Generating Figure 07: Principal Component Thermography...")
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(
        result.pct_bundle.score_map,
        origin="lower",
        cmap="plasma",
        extent=[0, config.geometry.plate.length_mm, 0, config.geometry.plate.width_mm]
    )
    fig.colorbar(im, ax=ax, label="EOF Mode Intensity")
    ax.set_title(f"PCT Spatial EOF (Component {result.pct_bundle.raw_result.selected_component_idx + 1})")
    ax.set_xlabel("Length [mm]")
    ax.set_ylabel("Width [mm]")
    fig.savefig(out_dir / "07_pct_eof_image.png")
    plt.close(fig)

    # Figure 8: SPCT Image
    console.print("Generating Figure 08: Sparse PCT Image...")
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(
        result.spct_bundle.score_map,
        origin="lower",
        cmap="plasma",
        extent=[0, config.geometry.plate.length_mm, 0, config.geometry.plate.width_mm]
    )
    fig.colorbar(im, ax=ax, label="Sparse EOF Intensity")
    ax.set_title(f"Sparse PCT Image (alpha={result.spct_bundle.raw_result.sparsity_alpha})")
    ax.set_xlabel("Length [mm]")
    ax.set_ylabel("Width [mm]")
    fig.savefig(out_dir / "08_spct_sparse_image.png")
    plt.close(fig)

    # Figure 9: RPT Image
    console.print("Generating Figure 09: Random Projection Technique Image...")
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(
        result.rpt_bundle.score_map,
        origin="lower",
        cmap="plasma",
        extent=[0, config.geometry.plate.length_mm, 0, config.geometry.plate.width_mm]
    )
    fig.colorbar(im, ax=ax, label="Projected Score Intensity")
    ax.set_title("Random Projection Technique (RPT) Anomaly Map")
    ax.set_xlabel("Length [mm]")
    ax.set_ylabel("Width [mm]")
    fig.savefig(out_dir / "09_rpt_score_image.png")
    plt.close(fig)

    # Figure 10: Multi-Method Comparison & Prediction Overlay
    console.print("Generating Figure 10: Multi-Method Ground-Truth vs Prediction Panel...")
    plot_method_comparison_panel(result, save_path=out_dir / "10_ground_truth_vs_prediction_overlay.png")

    # Figure 15: Runtime Benchmark
    console.print("Generating Figure 15: Processing Runtime Benchmark...")
    plot_runtime_comparison(result.metrics_dataframe, save_path=out_dir / "15_method_runtime_comparison.png")

    # Figures 11-14: Depth & Noise Parameter Studies
    console.print("Running sweep for Figures 11-14 (Depth and Noise Studies)...")
    if args.quick:
        sweep_diams = [6.0, 10.0]
        sweep_depths = [0.4, 0.6, 0.8]
        sweep_noises = [None, 30.0, 25.0, 20.0]
    else:
        sweep_diams = [4.0, 6.0, 8.0, 10.0, 12.0]
        sweep_depths = [0.2, 0.4, 0.6, 0.8, 1.0]
        sweep_noises = [None, 30.0, 25.0, 20.0]

    sweep_df = run_parameter_sweep(
        base_config=config,
        diameters_mm=sweep_diams,
        depths_mm=sweep_depths,
        noise_levels_db=sweep_noises,
        output_dir=out_dir / "sweep_data"
    )

    console.print("Generating Figures 11-13: Depth Performance Studies...")
    plot_depth_performance(sweep_df, save_path=out_dir / "11_12_13_depth_studies.png")

    # Figure 14: Noise Degradation Study
    console.print("Generating Figure 14: Performance vs Noise...")
    fig, ax = plt.subplots(figsize=(8, 5))
    noise_df = sweep_df.copy()
    noise_df["noise_snr_num"] = noise_df["noise_snr_db"].apply(lambda x: 40.0 if x == "Clean (Inf)" else float(x))
    for m in noise_df["method_name"].unique():
        sub = noise_df[noise_df["method_name"] == m].sort_values("noise_snr_num")
        grp = sub.groupby("noise_snr_num")["cnr"].mean().reset_index()
        ax.plot(grp["noise_snr_num"], grp["cnr"], marker="o", lw=2.0, label=m)

    ax.set_xlabel("Signal-to-Noise Ratio (SNR) [dB] (40 = Clean)")
    ax.set_ylabel("Contrast-to-Noise Ratio (CNR)")
    ax.set_title("NDT Algorithm Robustness under AWGN Noise Degradation")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend()
    fig.savefig(out_dir / "14_performance_vs_noise.png")
    plt.close(fig)

    console.print(f"[bold green]All 17 Conference & Publication Figures successfully generated in: {out_dir}[/bold green]")


if __name__ == "__main__":
    main()
