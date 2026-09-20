#!/usr/bin/env python3
"""
Offline Web Asset Exporter for LFMT Visualizations.

Generates pre-rendered lightweight thermogram sequences, multi-method comparison
maps, and case metadata from cached FEM simulations without rerunning the solver.
"""

import copy
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from lfmt.config import load_config
from lfmt.simulation import SimulationResult
from lfmt.simulation.base import GroundTruth
from lfmt.camera import VirtualIRCamera
from lfmt.noise import apply_noise_pipeline
from lfmt.excitation import LFMTExcitation
from lfmt.pulse_compression import LFMTMatchedFilter
from lfmt.contrast import RawThermalContrast
from lfmt.pct import PrincipalComponentThermography
from lfmt.spct import SparsePrincipalComponentThermography
from lfmt.rpt import RandomProjectionTechnique
from lfmt.detection import DefectDetector
from lfmt.metrics import compute_metrics


def export_thermogram_assets(
    fem_cache_dir: Path = Path("data/generated/fem"),
    output_dir: Path = Path("web/public/thermograms")
) -> None:
    print("=" * 70)
    print("EXPORTING OFFLINE THERMOGRAM & CASE VISUAL ASSETS FOR WEB")
    print("=" * 70)
    output_dir.mkdir(parents=True, exist_ok=True)
    cases_dir = Path("web/public/cases")
    cases_dir.mkdir(parents=True, exist_ok=True)

    base_config = load_config("configs/default.yaml")
    fov = (100.0, 70.0)

    # Key representative cases to export for interactive explorer
    case_tags = [
        ("D080_Z004", 8.0, 0.4),
        ("D040_Z002", 4.0, 0.2),
        ("D060_Z004", 6.0, 0.4),
        ("D100_Z006", 10.0, 0.6),
        ("D120_Z008", 12.0, 0.8),
        ("HEALTHY_CONTROL", 0.0, 0.0)
    ]

    exc = LFMTExcitation(
        f0_hz=base_config.excitation.f0_hz,
        f1_hz=base_config.excitation.f1_hz,
        duration_s=base_config.excitation.duration_s,
        q0_w_m2=base_config.excitation.q0_w_m2,
        sampling_rate_hz=base_config.camera.sampling_rate_hz
    )

    cases_index = []

    for tag, diam, depth in case_tags:
        case_path = fem_cache_dir / tag
        npz_file = case_path / "clean_thermograms.npz"
        gt_file = case_path / "ground_truth.json"

        if not npz_file.exists() or not gt_file.exists():
            print(f"[-] Skipping {tag}: Cache files not found.")
            continue

        print(f"[+] Processing case: {tag} (D={diam}mm, z={depth}mm)...")
        data = np.load(npz_file)
        surf_temp = data["surface_temperature"]
        t_vec = data["time_vector"]
        x_grid = data["x_grid_mm"]
        y_grid = data["y_grid_mm"]
        z_grid = data["z_grid_mm"]

        with open(gt_file, "r", encoding="utf-8") as f:
            gt_dict = json.load(f)
        gt = GroundTruth(**gt_dict)

        sim_res = SimulationResult(
            surface_temperature=surf_temp,
            time_vector=t_vec,
            x_grid_mm=x_grid,
            y_grid_mm=y_grid,
            z_grid_mm=z_grid,
            ground_truth=gt,
            backend_name="fem",
            metadata={}
        )

        cfg = copy.deepcopy(base_config)
        cfg.geometry.inclusion.diameter_mm = diam
        cfg.geometry.inclusion.depth_mm = depth
        cfg.geometry.inclusion.thickness_mm = 0.5 if diam > 0 else 0.0

        cam = VirtualIRCamera(cfg.camera)
        capture_clean = cam.capture(sim_res)
        gt_mask = capture_clean.ground_truth_mask
        frames = capture_clean.thermograms
        times_cam = capture_clean.time_vector

        # Export 10 key time frames as PNGs for sequence player
        frame_indices = np.linspace(0, len(frames) - 1, 10, dtype=int)
        case_therm_dir = output_dir / tag
        case_therm_dir.mkdir(parents=True, exist_ok=True)
        frame_metadata = []

        t_min_c = float(np.min(frames) - 273.15)
        t_max_c = float(np.max(frames) - 273.15)

        for i, idx in enumerate(frame_indices):
            t_val = float(times_cam[idx])
            frame_img = frames[idx] - 273.15  # Celsius
            fname = f"frame_{i:02d}.png"
            fpath = case_therm_dir / fname

            fig, ax = plt.subplots(figsize=(4, 2.8), dpi=100)
            im = ax.imshow(frame_img, cmap="inferno", extent=[0, 100, 0, 70], origin="lower", vmin=t_min_c, vmax=t_max_c)
            ax.set_title(f"t = {t_val:.1f} s", fontsize=10)
            ax.set_xlabel("x [mm]", fontsize=8)
            ax.set_ylabel("y [mm]", fontsize=8)
            ax.tick_params(labelsize=8)
            plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="T [°C]")
            plt.tight_layout()
            fig.savefig(fpath)
            plt.close(fig)

            frame_metadata.append({
                "frame_index": i,
                "time_seconds": round(t_val, 2),
                "image_url": f"/thermograms/{tag}/{fname}",
                "min_temp_c": round(float(np.min(frame_img)), 2),
                "max_temp_c": round(float(np.max(frame_img)), 2),
                "mean_temp_c": round(float(np.mean(frame_img)), 2)
            })

        # Process under 4 noise conditions for Multi-Method explorer
        noise_scenarios = [
            ("Clean", 0.0),
            ("30dB", 30.0),
            ("25dB", 25.0),
            ("20dB", 20.0)
        ]

        case_data_by_noise = {}

        for noise_label, snr_db in noise_scenarios:
            if snr_db > 0.0:
                n_cfg = copy.deepcopy(cfg.noise)
                n_cfg.snr_db = snr_db
                n_cfg.random_seed = 42
                therm = apply_noise_pipeline(capture_clean.thermograms, n_cfg)
            else:
                therm = capture_clean.thermograms

            raw_eng = RawThermalContrast(mode="blind")
            res_raw = raw_eng.process(therm, t_vec)
            mf_eng = LFMTMatchedFilter(excitation=exc)
            res_mf = mf_eng.process(therm, t_vec)
            pct_eng = PrincipalComponentThermography(n_components=6, mode="blind")
            res_pct = pct_eng.process(therm)
            spct_eng = SparsePrincipalComponentThermography(n_components=4, alpha=0.05, max_iter=30, mode="blind")
            res_spct = spct_eng.process(therm)
            rpt_eng = RandomProjectionTechnique(n_components=6, mode="blind")
            res_rpt = rpt_eng.process(therm)

            detector = DefectDetector(threshold_method="adaptive_otsu", min_area_px=3)
            det_raw = detector.detect(res_raw.contrast_map, fov_mm=fov)
            det_mf = detector.detect(res_mf.normalized_map, fov_mm=fov)
            det_pct = detector.detect(res_pct.selected_eof_image, fov_mm=fov)
            det_spct = detector.detect(res_spct.selected_sparse_image, fov_mm=fov)
            det_rpt = detector.detect(res_rpt.selected_rpt_image, fov_mm=fov)

            met_raw = compute_metrics("Raw Contrast", det_raw, gt, gt_mask, res_raw.contrast_map, res_raw.runtime_seconds, fov)
            met_mf = compute_metrics("Matched Filter", det_mf, gt, gt_mask, res_mf.normalized_map, res_mf.runtime_seconds, fov)
            met_pct = compute_metrics("PCT", det_pct, gt, gt_mask, res_pct.selected_eof_image, res_pct.runtime_seconds, fov)
            met_spct = compute_metrics("SPCT", det_spct, gt, gt_mask, res_spct.selected_sparse_image, res_spct.runtime_seconds, fov)
            met_rpt = compute_metrics("RPT", det_rpt, gt, gt_mask, res_rpt.selected_rpt_image, res_rpt.runtime_seconds, fov)

            # Export combined 6-panel comparison image
            fig, axes = plt.subplots(2, 3, figsize=(9, 5.5), dpi=120)
            maps = [
                ("Ground Truth Mask", gt_mask.astype(float), "Blues"),
                ("Raw Thermal Contrast", res_raw.contrast_map, "inferno"),
                ("Matched Filter (Pulse Comp.)", res_mf.normalized_map, "magma"),
                ("PCT (EOF Spatial Mode)", res_pct.selected_eof_image, "plasma"),
                ("SPCT (Sparse PCA Mode)", res_spct.selected_sparse_image, "viridis"),
                ("RPT (Random Projection)", res_rpt.selected_rpt_image, "cividis")
            ]
            for ax, (title, m_arr, cmap) in zip(axes.ravel(), maps):
                im = ax.imshow(m_arr, cmap=cmap, extent=[0, 100, 0, 70], origin="lower")
                ax.set_title(title, fontsize=8, fontweight="bold")
                ax.set_xticks([0, 50, 100])
                ax.set_yticks([0, 35, 70])
                ax.tick_params(labelsize=7)
                plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            fig.suptitle(f"{tag} — Noise: {noise_label}", fontsize=10, fontweight="bold")
            plt.tight_layout()
            comp_name = f"comparison_{noise_label.lower()}.png"
            comp_path = case_therm_dir / comp_name
            fig.savefig(comp_path)
            plt.close(fig)

            case_data_by_noise[noise_label] = {
                "comparison_image_url": f"/thermograms/{tag}/{comp_name}",
                "metrics": [
                    met_raw.to_dict(),
                    met_mf.to_dict(),
                    met_pct.to_dict(),
                    met_spct.to_dict(),
                    met_rpt.to_dict()
                ]
            }

        case_manifest = {
            "case_tag": tag,
            "diameter_mm": diam,
            "depth_mm": depth,
            "is_healthy": (diam <= 0.0),
            "ground_truth": gt.to_dict(),
            "frames": frame_metadata,
            "noise_scenarios": case_data_by_noise
        }

        with open(cases_dir / f"{tag}.json", "w", encoding="utf-8") as f:
            json.dump(case_manifest, f, indent=2)

        cases_index.append({
            "case_tag": tag,
            "diameter_mm": diam,
            "depth_mm": depth,
            "is_healthy": (diam <= 0.0),
            "preview_url": f"/thermograms/{tag}/frame_05.png"
        })

    with open(cases_dir / "index.json", "w", encoding="utf-8") as f:
        json.dump(cases_index, f, indent=2)

    print(f"[+] Successfully exported {len(cases_index)} case visual packages to web/public/")
    print("=" * 70)


if __name__ == "__main__":
    export_thermogram_assets()