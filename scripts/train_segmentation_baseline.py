"""Train a small synthetic-only segmentation network on off-benchmark geometries."""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lfmt.camera import VirtualIRCamera
from lfmt.config import load_config
from lfmt.ml.segmenter import TemporalPixelSegmenter, features
from lfmt.noise import add_awgn_noise
from lfmt.simulation import get_simulation_backend


def main() -> None:
    out = ROOT / "results/conference/analysis/tier2"
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(2026)
    x_parts, y_parts, cases, validation = [], [], [], []
    # Geometry split, not pixel split. None coincides with the conference grid.
    geometries = [(5., .3), (7., .5), (9., .7), (11., .9), (5., .7), (9., .3), (0., .5), (0., .7), (7., .9), (11., .3)]
    held_out = [(6.5, .55), (10.5, .75), (0., .65)]
    for index, (diameter, depth) in enumerate(geometries + held_out):
        cfg = load_config(ROOT / "configs/default.yaml")
        cfg.simulation.backend = "fem"
        cfg.simulation.spatial_resolution = {"nx": 30, "ny": 22, "nz": 12}
        cfg.simulation.timestep_s = .1
        cfg.simulation.total_time_s = 14.
        cfg.camera.resolution_x = cfg.camera.resolution_y = 32
        cfg.camera.sampling_rate_hz = 10.
        cfg.geometry.inclusion.diameter_mm = diameter
        cfg.geometry.inclusion.depth_mm = depth
        cfg.geometry.inclusion.center_x_mm = float(rng.uniform(30, 70))
        cfg.geometry.inclusion.center_y_mm = float(rng.uniform(22, 48))
        sim = get_simulation_backend("fem").run(cfg)
        capture = VirtualIRCamera(cfg.camera).capture(sim)
        split = "train" if index < len(geometries) else "validation"
        cases.append(dict(split=split, config=asdict(cfg)))
        for noise in [None, 30., 20.]:
            cube = add_awgn_noise(capture.thermograms, noise, seed=20000 + index)
            if split == "train":
                x_parts.append(features(cube))
                y_parts.append(capture.ground_truth_mask.ravel().astype(float))
            else:
                validation.append((diameter, depth, noise, cube, capture.ground_truth_mask))
        print(f"Simulated {split} D={diameter}, z={depth}", flush=True)
    model = TemporalPixelSegmenter()
    loss = model.fit(np.concatenate(x_parts), np.concatenate(y_parts))
    path = out / "temporal_pixel_v1.json"
    model.save(path)
    scores = []
    for diameter, depth, noise, cube, mask in validation:
        predicted = model.predict(cube) >= .5
        union = int((predicted | mask).sum())
        scores.append(dict(diameter_mm=diameter, depth_mm=depth, snr_db=noise,
                           iou=float((predicted & mask).sum() / union) if union else 1.,
                           foreground_fraction=float(predicted.mean())))
    report = dict(version="synthetic-segmenter-v1", seed=2026, cases=cases,
                  initial_loss=loss[0], final_loss=loss[-1], validation=scores,
                  checkpoint_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  limitations="Synthetic-only small baseline, coarse mesh, balanced pixel loss, fixed 14s acquisition. Validation geometries are disjoint; no experimental validation or superiority claim.")
    (out / "training_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Training loss: {loss[0]:.6f} -> {loss[-1]:.6f}")


if __name__ == "__main__":
    main()
