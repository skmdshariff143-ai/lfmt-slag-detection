"""Recover plots/provenance after a post-evaluation plotting failure; no raw writes."""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from lfmt.config import load_config
from scripts.run_conference_study import generate_all_conference_figures, simulate_or_load_clean_fem


def main() -> None:
    out = ROOT / "results/conference/analysis/tier2/benchmark_v2_2"
    raw_path = out / "raw_results.csv"
    raw_hash = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    data = pd.read_csv(raw_path)
    sensitivity = pd.read_csv(out / "sensitivity_summary.csv")
    coverage = json.loads((out / "coverage_verification.json").read_text())
    if coverage.get("validation") != "passed" or coverage.get("records") != len(data):
        raise ValueError("Run coverage validation before finalizing")
    cfg = load_config(ROOT / "configs/conference_v2_experimental.yaml")
    _, capture, _ = simulate_or_load_clean_fem(cfg, out / "cache/fem")
    generate_all_conference_figures(data, sensitivity, out / "figures", capture, cfg)
    if hashlib.sha256(raw_path.read_bytes()).hexdigest() != raw_hash:
        raise ValueError("Raw results unexpectedly changed")
    model = out.parent / "temporal_pixel_v1.json"
    manifest = dict(pipeline_version="experimental-v2.2", status="completed_after_plot_backend_repair",
                    total_records=len(data), source_git_commit=data.git_commit.unique().tolist(),
                    raw_sha256=raw_hash, config=asdict(cfg),
                    checkpoint_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),
                    source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in [ROOT / "scripts/run_conference_study.py", ROOT / "src/lfmt/advanced_processing.py", ROOT / "src/lfmt/ml/segmenter.py"]},
                    total_execution_time_s=None,
                    note="Original evaluation and sensitivity completed; Tk plotting failed before the original manifest. Figures regenerated with Agg without modifying raw results. End-to-end runtime unavailable.")
    (out / "experiment_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Finalized {len(data)} existing records; raw SHA256 unchanged: {raw_hash}")


if __name__ == "__main__":
    main()
