"""Trace cached conference maps without modifying the detector or frozen results."""
from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.ndimage import binary_opening, binary_closing, label

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lfmt.camera import VirtualIRCamera
from lfmt.config import load_config
from lfmt.detection import compute_otsu_threshold
from lfmt.noise import apply_noise_pipeline
from lfmt.pct import PrincipalComponentThermography
from lfmt.rpt import RandomProjectionTechnique
from lfmt.spct import SparsePrincipalComponentThermography
from lfmt.simulation.base import GroundTruth, SimulationResult


def main() -> None:
    cfg = load_config(ROOT / "configs/default.yaml")
    cfg.camera.resolution_x = cfg.camera.resolution_y = 32
    cfg.camera.sampling_rate_hz = 10
    cfg.noise.snr_db = 30
    cfg.noise.seed = 1001
    rows = []
    paths = sorted((ROOT / "data/generated/fem").glob("D*/clean_thermograms.npz"))
    if len(paths) != 25:
        raise ValueError(f"Expected 25 cached geometries, found {len(paths)}; no cache was regenerated")
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    for path in paths:
        data = np.load(path)
        gt = GroundTruth(**json.loads((path.parent / "ground_truth.json").read_text()))
        sim = SimulationResult(surface_temperature=data["surface_temperature"], time_vector=data["time_vector"],
                               x_grid_mm=data["x_grid_mm"], y_grid_mm=data["y_grid_mm"], z_grid_mm=data["z_grid_mm"],
                               ground_truth=gt, backend_name="fem", metadata={})
        capture = VirtualIRCamera(cfg.camera).capture(sim)
        for condition, tensor in [("Clean", capture.thermograms), ("SNR 30 dB", apply_noise_pipeline(capture.thermograms, cfg.noise))]:
            engines = [("PCT", PrincipalComponentThermography(), "selected_eof_image"),
                       ("RPT", RandomProjectionTechnique(), "selected_rpt_image"),
                       ("SPCT", SparsePrincipalComponentThermography(), "selected_sparse_image")]
            for method, engine, attr in engines:
                result = engine.process(tensor)
                score = getattr(result, attr)
                normalized = (score - score.min()) / np.ptp(score) if np.ptp(score) > 1e-12 else np.zeros_like(score)
                threshold = compute_otsu_threshold(normalized)
                raw = normalized >= threshold
                opened = binary_opening(raw, structure=np.ones((3, 3)))
                closed = binary_closing(opened, structure=np.ones((3, 3)))
                _, components = label(closed, structure=np.ones((3, 3)))
                rows.append(dict(case=path.parent.name, diameter_mm=gt.diameter_mm, depth_mm=gt.depth_mm,
                                 method=method, condition=condition, selected_component=result.selected_component_idx,
                                 score_range=float(np.ptp(score)), otsu=threshold, raw_pixels=int(raw.sum()),
                                 opened_pixels=int(opened.sum()), closed_pixels=int(closed.sum()),
                                 raw_gt_overlap=int((raw & capture.ground_truth_mask).sum()),
                                 closed_gt_overlap=int((closed & capture.ground_truth_mask).sum()), components=int(components)))
        print(path.parent.name, flush=True)
    out = ROOT / "results/conference/analysis"
    pd.DataFrame(rows).to_csv(out / "clean_threshold_trace.csv", index=False)
    (out / "threshold_trace_manifest.json").write_text(json.dumps({
        "cache_sha256": hashes, "camera_resolution": [32, 32], "sampling_rate_hz": 10,
        "noise_seed": 1001, "note": "Clean morphology replay; noisy mechanism experiment uses current noise code."
    }, indent=2) + "\n", encoding="utf-8")
    print(pd.DataFrame(rows).groupby(["method", "condition"])[["raw_pixels", "opened_pixels", "closed_gt_overlap"]].mean())


if __name__ == "__main__":
    main()
