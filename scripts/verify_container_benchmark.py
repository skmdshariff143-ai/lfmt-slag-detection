"""Recompute two deterministic benchmark cases against the versioned Tier 2 run.

This canary covers clean D=4/z=0.2 and healthy controls, all eight methods. It is
not a claim to reproduce every historical seed or the frozen audited dataset.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from lfmt.camera import VirtualIRCamera
from lfmt.config import load_config
from lfmt.ml import TemporalPixelSegmenter
from lfmt.simulation import get_simulation_backend
from scripts.run_conference_study import execute_processing_pipeline


def main() -> None:
    config = load_config(ROOT / "configs/conference_v2_experimental.yaml")
    model = TemporalPixelSegmenter.load(ROOT / "results/conference/analysis/tier2/temporal_pixel_v1.json")
    baseline = pd.read_csv(ROOT / "results/conference/analysis/tier2/benchmark_v2_2/raw_results.csv")
    count = 0
    for diameter, depth in [(4., .2), (0., 0.)]:
        cfg = copy.deepcopy(config)
        cfg.geometry.inclusion.diameter_mm = diameter
        cfg.geometry.inclusion.depth_mm = depth
        result = get_simulation_backend("fem").run(cfg)
        assert result.backend_name == "fem", "FEM fallback invalidates reproduction"
        capture = VirtualIRCamera(cfg.camera).capture(result)
        metrics = execute_processing_pipeline(capture.thermograms, capture.time_vector, cfg,
                                              capture.ground_truth, capture.ground_truth_mask, model)
        for metric in metrics:
            rows = baseline[(baseline.diameter_mm == diameter) & (baseline.depth_mm == depth)
                            & (baseline.noise_condition == "Clean") & (baseline.method == metric.method_name)]
            assert len(rows) == 1
            expected = rows.iloc[0]
            assert bool(metric.candidate_detected) == bool(expected.candidate_detected), metric.method_name
            assert bool(metric.is_detected and diameter > 0) == bool(expected.is_detected), metric.method_name
            np.testing.assert_allclose([metric.iou, metric.cnr], [expected.iou, expected.cnr],
                                       rtol=1e-6, atol=1e-8, err_msg=metric.method_name)
            count += 1
    print(f"Container benchmark canary: {count} method/case comparisons passed")


if __name__ == "__main__":
    main()
