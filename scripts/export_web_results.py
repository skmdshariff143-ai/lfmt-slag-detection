#!/usr/bin/env python3
"""
Web Data Export Script for LFMT Conference Benchmark Results.

Exports frozen verified conference results (CSV + JSON) into a lightweight,
structured directory `web_data/` with full provenance metadata ready for
front-end consumption or web visualization.
"""

import json
import os
import shutil
import sys
from pathlib import Path
import pandas as pd


def export_web_data(
    source_dir: Path = Path("results/conference/final"),
    target_dir: Path = Path("web_data")
) -> None:
    print("=" * 70)
    print("EXPORTING VERIFIED BENCHMARK RESULTS FOR WEB CONSUMPTION")
    print(f"Source: {source_dir}")
    print(f"Target: {target_dir}")
    print("=" * 70)

    target_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load manifest
    manifest_src = source_dir / "experiment_manifest_final.json"
    if not manifest_src.exists():
        manifest_src = source_dir.parent / "experiment_manifest.json"

    if manifest_src.exists():
        with open(manifest_src, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
    else:
        manifest_data = {}

    web_manifest = {
        "dataset_version": "2.1.0-final-audited",
        "dataset_name": "LFMT Mild Steel Slag Detection Benchmark",
        "protocol_version": "blind-v2-audited",
        "git_commit_sha": manifest_data.get("git_commit_sha", "unknown"),
        "timestamp_utc": manifest_data.get("timestamp_utc", ""),
        "solver_backend": manifest_data.get("solver_backend", "fem"),
        "total_evaluations": manifest_data.get("total_records", 4030),
        "materials": manifest_data.get("materials", {}),
        "geometries": manifest_data.get("geometries_evaluated", {}),
        "noise_protocol": manifest_data.get("noise_protocol", {})
    }

    with open(target_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(web_manifest, f, indent=2)
    print(f"[+] Exported: {target_dir / 'manifest.json'}")

    # 2. Export summary files
    files_to_export = [
        ("summary_by_method_final.csv", "summary_by_method.json", "summary_by_method.csv"),
        ("summary_by_depth_final.csv", "summary_by_depth.json", "summary_by_depth.csv"),
        ("summary_by_diameter_final.csv", "summary_by_diameter.json", "summary_by_diameter.csv"),
        ("summary_by_noise_final.csv", "summary_by_noise.json", "summary_by_noise.csv"),
        ("healthy_specificity_final.csv", "healthy_specificity.json", "healthy_specificity.csv"),
        ("max_detectable_depth_final.csv", "max_detectable_depth.json", "max_detectable_depth.csv"),
        ("sensitivity_final.csv", "sensitivity_summary.json", "sensitivity_summary.csv"),
    ]

    for src_name, json_name, csv_name in files_to_export:
        src_path = source_dir / src_name
        if not src_path.exists():
            # fallback to non-_final name in parent
            alt_name = src_name.replace("_final", "").replace("sensitivity_final", "sensitivity_summary")
            src_path = source_dir.parent / alt_name

        if src_path.exists():
            df = pd.read_csv(src_path)
            # Save JSON
            df.to_json(target_dir / json_name, orient="records", indent=2)
            # Save CSV
            df.to_csv(target_dir / csv_name, index=False)
            print(f"[+] Exported: {json_name} and {csv_name} ({len(df)} rows)")
        else:
            print(f"[-] Warning: Source file not found: {src_path}")

    print("=" * 70)
    print("WEB DATA EXPORT COMPLETED SUCCESSFULLY.")
    print("=" * 70)


if __name__ == "__main__":
    export_web_data()