"""
High-Resolution Publication & Conference Visualizations.

Generates conference-ready 300+ DPI plots with standard IEEE/Elsevier typography,
consistent colormaps (inferno, viridis, magma, bwr), scale bars, physical coordinate axes,
and multi-panel comparison layouts.
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd

from lfmt.excitation import LFMTExcitation
from lfmt.experiments import ExperimentCaseResult

# Set scientific plotting style
plt.rcParams.update({
    "font.size": 11,
    "font.family": "sans-serif",
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})


def plot_excitation_waveform(
    excitation: LFMTExcitation,
    total_time_s: float = 12.0,
    save_path: Optional[str | Path] = None
) -> plt.Figure:
    """Figure 1 & 2: LFMT Heat Flux & Instantaneous Chirp Frequency."""
    t = excitation.compute_time_vector(total_time_s)
    q = excitation.heat_flux(t)
    f = excitation.instantaneous_frequency(t)
    _phi = excitation.instantaneous_phase(t)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

    # Subplot 1: Heat Flux
    ax1.plot(t, q / 1e3, color="#d90429", lw=2.0, label=r"$q(t) = q_0 [1 + \sin(\phi(t))]$")
    ax1.axvline(excitation.duration_s, color="black", linestyle="--", alpha=0.7, label="End of Excitation")
    ax1.set_ylabel(r"Heat Flux $\left[\mathrm{kW/m^2}\right]$")
    ax1.set_title("Linear Frequency-Modulated Thermal Excitation (LFMT Chirp)")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper right")
    ax1.set_ylim(bottom=-0.2)

    # Subplot 2: Instantaneous Frequency
    ax2.plot(t, f, color="#0077b6", lw=2.0, label=r"$f(t) = f_0 + \beta t$")
    ax2.set_xlabel("Time [s]")
    ax2.set_ylabel("Inst. Frequency [Hz]")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper left")

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path)
    return fig


def plot_thermogram_progression(
    result: ExperimentCaseResult,
    frame_indices: Optional[List[int]] = None,
    save_path: Optional[str | Path] = None
) -> plt.Figure:
    """Figure 3: Multi-frame thermogram progression sequence."""
    tensor = result.capture_noisy.thermograms
    time_vec = result.capture_noisy.time_vector
    n_frames = tensor.shape[0]

    if frame_indices is None:
        frame_indices = np.linspace(0, n_frames - 1, 6, dtype=int).tolist()

    n_plots = len(frame_indices)
    fig, axes = plt.subplots(1, n_plots, figsize=(3.2 * n_plots, 3.2))

    vmin, vmax = np.min(tensor), np.max(tensor)

    for i, idx in enumerate(frame_indices):
        ax = axes[i]
        t_val = time_vec[idx]
        im = ax.imshow(
            tensor[idx] - 273.15,
            origin="lower",
            cmap="inferno",
            extent=[0, result.config.geometry.plate.length_mm, 0, result.config.geometry.plate.width_mm],
            vmin=vmin - 273.15,
            vmax=vmax - 273.15
        )
        ax.set_title(f"t = {t_val:.1f} s (Frame {idx})", fontsize=11)
        ax.set_xlabel("Length [mm]")
        if i == 0:
            ax.set_ylabel("Width [mm]")
        else:
            ax.set_yticklabels([])

    cbar_ax = fig.add_axes([0.92, 0.25, 0.015, 0.5])
    cbar = fig.colorbar(im, cax=cbar_ax)
    cbar.set_label(r"Surface Temp [$^\circ\mathrm{C}$]")

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path)
    return fig


def plot_temporal_contrast_curves(
    result: ExperimentCaseResult,
    save_path: Optional[str | Path] = None
) -> plt.Figure:
    """Figure 4 & 5: Defect vs Sound temperature and differential contrast curves."""
    raw_res = result.contrast_bundle.raw_result
    t = raw_res.time_vector

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    # Defect vs Sound
    ax1.plot(t, raw_res.t_defect_curve - 273.15, color="#d90429", lw=2.0, label="Defect Region")
    ax1.plot(t, raw_res.t_sound_curve - 273.15, color="#0077b6", lw=2.0, linestyle="--", label="Sound Steel Region")
    ax1.set_xlabel("Time [s]")
    ax1.set_ylabel(r"Temperature [$^\circ\mathrm{C}$]")
    ax1.set_title("Thermal Transient Evolution")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend()

    # Differential Contrast
    ax2.plot(t, raw_res.delta_t_curve, color="#7209b7", lw=2.0, label=r"$\Delta T(t) = T_{defect} - T_{sound}$")
    ax2.axvline(raw_res.t_max_contrast_s, color="black", linestyle=":", label=f"Max Contrast at {raw_res.t_max_contrast_s:.2f} s")
    ax2.set_xlabel("Time [s]")
    ax2.set_ylabel(r"Differential Contrast $\Delta T$ [K]")
    ax2.set_title(r"Differential Thermal Contrast Curve $\Delta T(t)$")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend()

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path)
    return fig


def plot_method_comparison_panel(
    result: ExperimentCaseResult,
    save_path: Optional[str | Path] = None
) -> plt.Figure:
    """Multi-method comparison: Ground Truth, Raw Contrast, Matched Filter, PCT, SPCT, RPT."""
    methods = [
        ("Raw Contrast", result.contrast_bundle),
        ("Matched Filter", result.matched_filter_bundle),
        ("PCT", result.pct_bundle),
        ("SPCT", result.spct_bundle),
        ("RPT", result.rpt_bundle),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(13, 8))
    axes = axes.flatten()

    L_x = result.config.geometry.plate.length_mm
    L_y = result.config.geometry.plate.width_mm
    extent = [0, L_x, 0, L_y]

    # Panel 0: Ground Truth
    gt_mask = result.capture_clean.ground_truth_mask
    axes[0].imshow(gt_mask, origin="lower", cmap="gray", extent=extent)
    gt = result.capture_clean.ground_truth
    circle = patches.Circle((gt.center_x_mm, gt.center_y_mm), gt.diameter_mm / 2.0, fill=False, edgecolor="lime", lw=2.0)
    axes[0].add_patch(circle)
    axes[0].set_title(f"Ground Truth (D={gt.diameter_mm:.1f}mm, z={gt.depth_mm:.1f}mm)")
    axes[0].set_xlabel("X [mm]")
    axes[0].set_ylabel("Y [mm]")

    # Panels 1-5: Processed Images with Segmentation Contours
    for idx, (name, bundle) in enumerate(methods, start=1):
        ax = axes[idx]
        score = bundle.score_map
        _im = ax.imshow(score, origin="lower", cmap="plasma", extent=extent)
        
        # Overlay detected contour / centroid
        if bundle.detection.is_detected:
            pred_cx, pred_cy = bundle.detection.centroid_mm
            pred_r = bundle.detection.equivalent_diameter_mm / 2.0
            pred_circle = patches.Circle((pred_cx, pred_cy), pred_r, fill=False, edgecolor="cyan", lw=2.0, linestyle="--", label="Detected")
            ax.add_patch(pred_circle)
            ax.plot(pred_cx, pred_cy, "c+", markersize=10, markeredgewidth=2)

        # Also overlay true circle in lime for visual comparison
        true_circle = patches.Circle((gt.center_x_mm, gt.center_y_mm), gt.diameter_mm / 2.0, fill=False, edgecolor="lime", lw=1.5, label="True Defect")
        ax.add_patch(true_circle)

        ax.set_title(f"{name} (IoU={bundle.metrics.iou:.2f}, CNR={bundle.metrics.cnr:.1f})")
        ax.set_xlabel("X [mm]")
        if idx % 3 == 0:
            ax.set_ylabel("Y [mm]")
        else:
            ax.set_yticklabels([])

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path)
    return fig


def plot_depth_performance(
    sweep_df: pd.DataFrame,
    save_path: Optional[str | Path] = None
) -> plt.Figure:
    """Figure 11-13: Contrast, IoU, and Localization Error vs Defect Depth."""
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 4.5))

    methods = sweep_df["method_name"].unique()
    colors = {"Raw Contrast": "#e76f51", "Matched Filter": "#2a9d8f", "PCT": "#264653", "SPCT": "#e9c46a", "RPT": "#9b5de5"}

    for m in methods:
        sub = sweep_df[sweep_df["method_name"] == m].sort_values("depth_mm")
        grouped = sub.groupby("depth_mm").mean(numeric_only=True).reset_index()
        c = colors.get(m, "blue")

        ax1.plot(grouped["depth_mm"], grouped["cnr"], marker="o", lw=2.0, color=c, label=m)
        ax2.plot(grouped["depth_mm"], grouped["iou"], marker="s", lw=2.0, color=c, label=m)
        ax3.plot(grouped["depth_mm"], grouped["localization_error_mm"], marker="^", lw=2.0, color=c, label=m)

    ax1.set_xlabel("Inclusion Depth [mm]")
    ax1.set_ylabel("Contrast-to-Noise Ratio (CNR)")
    ax1.set_title("CNR vs Depth")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend()

    ax2.set_xlabel("Inclusion Depth [mm]")
    ax2.set_ylabel("Intersection over Union (IoU)")
    ax2.set_title("Segmentation Overlap (IoU) vs Depth")
    ax2.grid(True, linestyle=":", alpha=0.6)

    ax3.set_xlabel("Inclusion Depth [mm]")
    ax3.set_ylabel("Localization Error [mm]")
    ax3.set_title("Localization Error vs Depth")
    ax3.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path)
    return fig


def plot_runtime_comparison(
    metrics_df: pd.DataFrame,
    save_path: Optional[str | Path] = None
) -> plt.Figure:
    """Figure 15: Execution time across all processing techniques."""
    fig, ax = plt.subplots(figsize=(7, 4))
    methods = metrics_df["method_name"].tolist()
    times_ms = [t * 1e3 for t in metrics_df["runtime_s"].tolist()]

    colors = ["#e76f51", "#2a9d8f", "#264653", "#e9c46a", "#9b5de5"]
    bars = ax.bar(methods, times_ms, color=colors[:len(methods)], edgecolor="black", width=0.55)

    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.5, f"{yval:.1f} ms", ha="center", va="bottom", fontsize=10)

    ax.set_ylabel("Execution Time [ms]")
    ax.set_title("Thermogram Signal Processing Runtime Comparison")
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path)
    return fig
