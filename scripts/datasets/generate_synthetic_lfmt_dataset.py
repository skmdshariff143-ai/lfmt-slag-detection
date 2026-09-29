#!/usr/bin/env python3
"""
Synthetic LFMT Multi-Task Dataset Generator.

Generates systematic train/val/test splits for:
1. Multi-Task Deep Learning (Thermal Maps + Physics Vector -> Class, Mask, Depth, Diam, Centroid)
2. Tabular Classical ML (14D Physics Features -> Class, Depth, Diam)

Guarantees strict case-level specimen isolation to prevent data leakage.
"""

from __future__ import annotations
import os
import math
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
from rich.console import Console
from rich.progress import Progress

from lfmt.analysis.physics_features import PhysicsFeatureEngine
from lfmt.excitation import LFMTExcitation


CLASS_NAMES = ["HEALTHY", "SLAG_INCLUSION", "WALL_THINNING", "AIR_VOID"]


def generate_single_synthetic_sample(
    sample_id: str,
    defect_type: str,
    depth_mm: float,
    diameter_mm: float,
    centroid_mm: Tuple[float, float],
    f0_hz: float = 0.05,
    f1_hz: float = 0.50,
    duration_s: float = 10.0,
    fps: float = 5.0,
    grid_size: Tuple[int, int] = (48, 48),
    fov_mm: Tuple[float, float] = (100.0, 70.0),
    snr_db: float = 25.0,
    rng: np.random.Generator = None
) -> Dict[str, Any]:
    """Generate a single physics-grounded synthetic sample."""
    if rng is None:
        rng = np.random.default_rng()

    H, W = grid_size
    n_frames = int(duration_s * fps)
    t_vec = np.linspace(0, duration_s, n_frames)
    dx_mm = fov_mm[0] / max(1, W - 1)
    dy_mm = fov_mm[1] / max(1, H - 1)

    # 1. 2D Coordinate grid [mm]
    y_coords = np.linspace(0, fov_mm[1], H)
    x_coords = np.linspace(0, fov_mm[0], W)
    xx, yy = np.meshgrid(x_coords, y_coords)

    # 2. Defect Mask & Spatial Profile
    cx_mm, cy_mm = centroid_mm
    r_mm = diameter_mm / 2.0
    dist_map = np.sqrt((xx - cx_mm) ** 2 + (yy - cy_mm) ** 2)
    
    if defect_type == "HEALTHY":
        seg_mask = np.zeros((H, W), dtype=bool)
        spatial_profile = np.zeros((H, W), dtype=float)
        contrast_amp = 0.0
    else:
        seg_mask = (dist_map <= r_mm)
        # Smooth thermal diffusion bell profile
        spatial_profile = np.exp(-0.5 * (dist_map / max(0.5, r_mm * 0.8)) ** 2)
        # Physics thermal resistance ~ diameter / (depth + 0.1)
        base_contrast = 1.8 * (diameter_mm / 6.0) / max(0.2, depth_mm + 0.1)
        if defect_type == "WALL_THINNING":
            contrast_amp = base_contrast * 1.4
        elif defect_type == "AIR_VOID":
            contrast_amp = base_contrast * 1.8  # Air has extremely low conductivity
        else:  # SLAG_INCLUSION
            contrast_amp = base_contrast * 1.0

    # 3. LFMT Chirp Temporal Modulation
    chirp_sig = np.sin(2 * np.pi * (f0_hz * t_vec + 0.5 * ((f1_hz - f0_hz) / duration_s) * (t_vec ** 2)))
    # Defect phase lag ~ depth * 0.4 s
    phase_lag_steps = int(min(n_frames // 4, depth_mm * fps * 0.4))
    if phase_lag_steps > 0:
        chirp_defect = np.roll(chirp_sig, phase_lag_steps)
    else:
        chirp_defect = chirp_sig

    # 4. Construct 3D Thermogram Cube
    cube = np.zeros((n_frames, H, W), dtype=np.float32) + 293.15  # 20 C ambient
    
    for k in range(n_frames):
        # Sound background warming
        cube[k, :, :] += 0.08 * t_vec[k]
        if defect_type != "HEALTHY":
            cube[k, :, :] += spatial_profile * (contrast_amp * 0.4 * chirp_defect[k] + contrast_amp * 0.6)

    # 5. Add Sensor Noise
    if snr_db is not None and snr_db > 0:
        sig_power = float(np.var(cube))
        noise_power = sig_power / (10.0 ** (snr_db / 10.0))
        noise = rng.normal(0, math.sqrt(max(1e-8, noise_power)), cube.shape).astype(np.float32)
        cube += noise

    # 6. Extract Spatiotemporal Features & Physics Context
    phys_ctx = PhysicsFeatureEngine.compute_physics_context("mild_steel", f0_hz, f1_hz)
    st_feats = PhysicsFeatureEngine.extract_spatiotemporal_features(cube, t_vec)

    # Physics vector for neural net: 8 elements
    phys_vec = np.array([
        phys_ctx.thermal_diffusivity_m2_s * 1e5,
        phys_ctx.thermal_effusivity_w_s12_m2k / 10000.0,
        f0_hz,
        f1_hz,
        fps,
        float(n_frames),
        st_feats.peak_delta_t_k,
        st_feats.time_to_peak_s
    ], dtype=np.float32)

    # Peak thermal contrast map (2D)
    mean_cube = np.mean(cube, axis=(1, 2))
    peak_idx = int(np.argmax(mean_cube))
    peak_map = (cube[peak_idx] - np.median(cube[peak_idx])).astype(np.float32)

    return {
        "sample_id": sample_id,
        "defect_type": defect_type,
        "class_id": CLASS_NAMES.index(defect_type),
        "depth_mm": float(depth_mm) if defect_type != "HEALTHY" else 0.0,
        "diameter_mm": float(diameter_mm) if defect_type != "HEALTHY" else 0.0,
        "centroid_mm": [float(cx_mm), float(cy_mm)] if defect_type != "HEALTHY" else [0.0, 0.0],
        "thermal_map": peak_map,
        "seg_mask": seg_mask.astype(np.float32),
        "physics_vec": phys_vec,
        "tabular_features": st_feats.raw_feature_vector.astype(np.float32),
        "f0_hz": f0_hz,
        "f1_hz": f1_hz,
        "duration_s": duration_s,
        "snr_db": snr_db
    }


def generate_dataset_split(
    split_name: str,
    n_samples: int,
    output_dir: Path,
    seed: int = 42
) -> Dict[str, Any]:
    """Generate a single split (train, val, or test)."""
    rng = np.random.default_rng(seed)
    
    maps_list = []
    masks_list = []
    phys_list = []
    tab_list = []
    classes_list = []
    depths_list = []
    diams_list = []
    centroids_list = []
    sample_ids = []

    defect_pool = ["HEALTHY", "SLAG_INCLUSION", "WALL_THINNING", "AIR_VOID"]

    for i in range(n_samples):
        s_id = f"{split_name}_{i:04d}"
        d_type = defect_pool[i % len(defect_pool)]
        
        depth = rng.uniform(0.2, 1.5) if d_type != "HEALTHY" else 0.0
        diam = rng.uniform(4.0, 12.0) if d_type != "HEALTHY" else 0.0
        cx = rng.uniform(25.0, 75.0) if d_type != "HEALTHY" else 50.0
        cy = rng.uniform(20.0, 50.0) if d_type != "HEALTHY" else 35.0
        snr = rng.choice([35.0, 30.0, 25.0, 20.0, 15.0])
        f0 = rng.choice([0.03, 0.05, 0.07])
        f1 = rng.choice([0.40, 0.50, 0.60])

        sample = generate_single_synthetic_sample(
            sample_id=s_id,
            defect_type=d_type,
            depth_mm=depth,
            diameter_mm=diam,
            centroid_mm=(cx, cy),
            f0_hz=f0,
            f1_hz=f1,
            duration_s=8.0,
            fps=5.0,
            grid_size=(48, 48),
            fov_mm=(100.0, 70.0),
            snr_db=snr,
            rng=rng
        )

        maps_list.append(sample["thermal_map"])
        masks_list.append(sample["seg_mask"])
        phys_list.append(sample["physics_vec"])
        tab_list.append(sample["tabular_features"])
        classes_list.append(sample["class_id"])
        depths_list.append(sample["depth_mm"])
        diams_list.append(sample["diameter_mm"])
        centroids_list.append(sample["centroid_mm"])
        sample_ids.append(s_id)

    # Save to NPZ
    out_file = output_dir / f"{split_name}.npz"
    np.savez_compressed(
        out_file,
        sample_ids=np.array(sample_ids),
        thermal_maps=np.array(maps_list, dtype=np.float32),
        seg_masks=np.array(masks_list, dtype=np.float32),
        physics_vectors=np.array(phys_list, dtype=np.float32),
        tabular_features=np.array(tab_list, dtype=np.float32),
        class_labels=np.array(classes_list, dtype=np.int64),
        depths=np.array(depths_list, dtype=np.float32),
        diameters=np.array(diams_list, dtype=np.float32),
        centroids=np.array(centroids_list, dtype=np.float32),
        class_names=np.array(CLASS_NAMES)
    )

    return {
        "split": split_name,
        "n_samples": n_samples,
        "file": str(out_file.name),
        "class_distribution": {c: int(sum(1 for cl in classes_list if cl == i)) for i, c in enumerate(CLASS_NAMES)}
    }


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic LFMT multi-task dataset.")
    parser.add_argument("--out-dir", type=str, default="data/datasets/synthetic_multitask_lfmt", help="Output directory")
    parser.add_argument("--train-samples", type=int, default=320, help="Number of training samples")
    parser.add_argument("--val-samples", type=int, default=80, help="Number of validation samples")
    parser.add_argument("--test-samples", type=int, default=100, help="Number of test samples")
    parser.add_argument("--seed", type=int, default=42, help="Master random seed")
    args = parser.parse_args()

    console = Console()
    console.print("[bold cyan]Generating Multi-Task Synthetic LFMT Dataset...[/bold cyan]")
    
    out_path = Path(args.out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    manifest: Dict[str, Any] = {
        "dataset_name": "Synthetic LFMT Multi-Task Thermography Dataset",
        "version": "v3.0-synthetic-prior",
        "description": "Systematic physics-informed synthetic LFMT thermogram dataset with defect characterization ground truths.",
        "classes": CLASS_NAMES,
        "splits": {}
    }

    train_meta = generate_dataset_split("train", args.train_samples, out_path, seed=args.seed)
    val_meta = generate_dataset_split("val", args.val_samples, out_path, seed=args.seed + 1)
    test_meta = generate_dataset_split("test", args.test_samples, out_path, seed=args.seed + 2)

    manifest["splits"] = {
        "train": train_meta,
        "val": val_meta,
        "test": test_meta
    }
    manifest["total_samples"] = args.train_samples + args.val_samples + args.test_samples

    manifest_path = out_path / "dataset_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    console.print(f"[bold green]Dataset generated successfully at {out_path} ({manifest['total_samples']} total samples).[/bold green]")


if __name__ == "__main__":
    main()
