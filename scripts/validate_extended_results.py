"""Validate coverage and paired inputs of an experimental eight-method run."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    data = pd.read_csv(args.directory / "raw_results.csv")
    expected = {"Raw Contrast", "Matched Filter", "PCT", "RPT", "SPCT", "TSR", "Chirp Phase Fusion", "Temporal Pixel Net"}
    if set(data.method) != expected:
        raise ValueError("Expected all eight benchmark methods")
    keys = ["diameter_mm", "depth_mm", "noise_condition", "noise_seed"]
    if data.duplicated(["method", *keys]).any():
        raise ValueError("Duplicate paired keys")
    pairing = data.pivot(index=keys, columns="method", values="iou")
    if pairing.isna().any().any() or len(pairing) != 806:
        raise ValueError("Incomplete paired conference coverage")
    if not np.isfinite(data[["iou", "cnr"]].to_numpy()).all():
        raise ValueError("Nonfinite score metrics")
    if not data.iou.between(0, 1).all():
        raise ValueError("IoU outside [0,1]")
    if data[data.is_healthy].is_detected.any():
        raise ValueError("Healthy controls cannot be true-positive detections")
    counts = data.groupby(["method", "is_healthy"]).size().unstack()
    if not (counts[False] == 775).all() or not (counts[True] == 31).all():
        raise ValueError("Expected 775 defect and 31 healthy runs per method")
    root = Path(__file__).resolve().parents[1]
    frozen_manifest = json.loads((root / "results/conference/analysis/analysis_manifest.json").read_text())
    for name, digest in frozen_manifest["frozen_sha256"].items():
        actual = hashlib.sha256((root / "results/conference/final" / name).read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError(f"Frozen input changed: {name}")
    result = dict(records=len(data), methods=sorted(expected), paired_inputs=len(pairing),
                  frozen_files_unchanged=True, validation="passed")
    (args.directory / "coverage_verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
