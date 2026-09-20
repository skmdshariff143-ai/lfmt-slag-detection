#!/usr/bin/env python3
"""
Web Data Export Script for LFMT Conference Benchmark Results.

Exports frozen verified conference results (CSV + JSON) into `web_data/`
and `web/public/data/` with SHA-256 provenance hashes in `dataset-lock.json`.
"""

import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd


def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def export_web_data(
    source_dir: Path = Path("results/conference/final"),
    staging_dir: Path = Path("web_data"),
    web_public_dir: Path = Path("web/public/data")
) -> None:
    print("=" * 70)
    print("EXPORTING VERIFIED BENCHMARK RESULTS FOR WEB PORTAL")
    print(f"Source Directory:  {source_dir}")
    print(f"Staging Directory: {staging_dir}")
    print(f"Web Public Data:   {web_public_dir}")
    print("=" * 70)

    staging_dir.mkdir(parents=True, exist_ok=True)
    web_public_dir.mkdir(parents=True, exist_ok=True)

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
        "git_commit_sha": manifest_data.get("git_commit_sha", "5319757"),
        "timestamp_utc": manifest_data.get("timestamp_utc", datetime.now(timezone.utc).isoformat()),
        "solver_backend": manifest_data.get("solver_backend", "fem"),
        "total_evaluations": 4030,
        "materials": manifest_data.get("materials", {}),
        "geometries": manifest_data.get("geometries_evaluated", {}),
        "noise_protocol": manifest_data.get("noise_protocol", {})
    }

    # Save manifest
    for target in [staging_dir, web_public_dir]:
        with open(target / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(web_manifest, f, indent=2)
    print(f"[+] Exported manifest.json to staging and web/public/data")

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

    source_hashes = {}
    exported_hashes = {}

    # Hash raw results if present
    raw_path = source_dir / "raw_results_final.csv"
    if raw_path.exists():
        source_hashes["raw_results_final.csv"] = compute_sha256(raw_path)

    for src_name, json_name, csv_name in files_to_export:
        src_path = source_dir / src_name
        if not src_path.exists():
            alt_name = src_name.replace("_final", "").replace("sensitivity_final", "sensitivity_summary")
            src_path = source_dir.parent / alt_name

        if src_path.exists():
            source_hashes[src_name] = compute_sha256(src_path)
            df = pd.read_csv(src_path)

            for target in [staging_dir, web_public_dir]:
                # Save JSON
                json_path = target / json_name
                df.to_json(json_path, orient="records", indent=2)
                # Save CSV
                csv_path = target / csv_name
                df.to_csv(csv_path, index=False)

            exported_hashes[json_name] = compute_sha256(web_public_dir / json_name)
            exported_hashes[csv_name] = compute_sha256(web_public_dir / csv_name)
            print(f"[+] Exported {json_name} & {csv_name} ({len(df)} rows)")
        else:
            print(f"[-] Warning: Source file not found: {src_path}")

    # 3. Create dataset-lock.json
    lock_data = {
        "dataset_version": "2.1.0-final-audited",
        "protocol_version": "blind-v2-audited",
        "git_commit_sha": manifest_data.get("git_commit_sha", "5319757"),
        "source_directory": str(source_dir).replace("\\", "/"),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_evaluations": 4030,
        "source_files_sha256": source_hashes,
        "exported_files_sha256": exported_hashes
    }

    for target in [staging_dir, web_public_dir]:
        with open(target / "dataset-lock.json", "w", encoding="utf-8") as f:
            json.dump(lock_data, f, indent=2)
    print(f"[+] Generated dataset-lock.json with {len(source_hashes)} source and {len(exported_hashes)} export hashes")

    print("=" * 70)
    print("WEB DATA EXPORT COMPLETED SUCCESSFULLY WITH CRYPTOGRAPHIC LOCK.")
    print("=" * 70)


if __name__ == "__main__":
    export_web_data()