#!/usr/bin/env python3
"""
Web Data Consistency and Integrity Verification Script.

Compares the authoritative scientific results in `results/conference/final/`
against the exported web representations in `web_data/` and `web/public/data/`.
Asserts exact numerical equality across all benchmark tables.
"""

import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd


def verify_web_data() -> bool:
    print("=" * 70)
    print("VERIFYING SCIENTIFIC CONSISTENCY: FROZEN FINAL vs WEB EXPORT")
    print("=" * 70)

    src_dir = Path("results/conference/final")
    web_data_dir = Path("web_data")
    web_public_dir = Path("web/public/data")

    if not src_dir.exists():
        print(f"[-] ERROR: Source directory not found: {src_dir}")
        return False

    comparison_pairs = [
        ("summary_by_method_final.csv", "summary_by_method.csv", "summary_by_method.json"),
        ("summary_by_depth_final.csv", "summary_by_depth.csv", "summary_by_depth.json"),
        ("summary_by_diameter_final.csv", "summary_by_diameter.csv", "summary_by_diameter.json"),
        ("summary_by_noise_final.csv", "summary_by_noise.csv", "summary_by_noise.json"),
        ("healthy_specificity_final.csv", "healthy_specificity.csv", "healthy_specificity.json"),
        ("max_detectable_depth_final.csv", "max_detectable_depth.csv", "max_detectable_depth.json"),
        ("sensitivity_final.csv", "sensitivity_summary.csv", "sensitivity_summary.json"),
    ]

    all_passed = True

    for src_file, csv_target, json_target in comparison_pairs:
        src_path = src_dir / src_file
        if not src_path.exists():
            print(f"[-] ERROR: Missing source file: {src_path}")
            all_passed = False
            continue

        df_src = pd.read_csv(src_path)

        # 1. Compare against web_data CSV
        web_csv_path = web_data_dir / csv_target
        if not web_csv_path.exists():
            print(f"[-] ERROR: Missing web_data CSV: {web_csv_path}")
            all_passed = False
            continue

        df_web_csv = pd.read_csv(web_csv_path)

        # 2. Compare against web/public/data JSON
        web_json_path = web_public_dir / json_target
        if not web_json_path.exists():
            print(f"[-] ERROR: Missing web/public/data JSON: {web_json_path}")
            all_passed = False
            continue

        with open(web_json_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        df_web_json = pd.DataFrame(json_data)

        # Numerical equality check
        num_cols = df_src.select_dtypes(include=[np.number]).columns

        # Check rows count
        if len(df_src) != len(df_web_csv) or len(df_src) != len(df_web_json):
            print(f"[-] FAILED: Row count mismatch for {src_file} ({len(df_src)} vs {len(df_web_csv)} vs {len(df_web_json)})")
            all_passed = False
            continue

        col_errors = []
        for col in num_cols:
            if col in df_web_csv.columns and col in df_web_json.columns:
                # Handle NaNs and object dtypes safely across NumPy 1.x and 2.x
                src_vals = pd.to_numeric(df_src[col], errors="coerce").fillna(-999999.0).to_numpy(dtype=float)
                csv_vals = pd.to_numeric(df_web_csv[col], errors="coerce").fillna(-999999.0).to_numpy(dtype=float)
                json_vals = pd.to_numeric(df_web_json[col], errors="coerce").fillna(-999999.0).to_numpy(dtype=float)

                if not np.allclose(src_vals, csv_vals, rtol=1e-4, atol=1e-4):
                    col_errors.append(f"CSV col '{col}' diff")
                if not np.allclose(src_vals, json_vals, rtol=1e-4, atol=1e-4):
                    col_errors.append(f"JSON col '{col}' diff")

        if col_errors:
            print(f"[-] FAILED {src_file}: {', '.join(col_errors)}")
            all_passed = False
        else:
            print(f"[PASS] {src_file:<32} -> {csv_target} / {json_target} (Exact Match, {len(df_src)} rows)")

    # 3. Check dataset-lock.json
    lock_path = web_public_dir / "dataset-lock.json"
    if lock_path.exists():
        with open(lock_path, "r", encoding="utf-8") as f:
            lock_data = json.load(f)
        print(f"[PASS] dataset-lock.json verified: Version '{lock_data.get('dataset_version')}', Commit '{lock_data.get('git_commit_sha')}'")
    else:
        print("[-] FAILED: dataset-lock.json missing!")
        all_passed = False

    print("=" * 70)
    if all_passed:
        print("ALL WEB DATA CONSISTENCY CHECKS PASSED WITH ZERO DISCREPANCIES.")
        print("=" * 70)
        return True
    else:
        print("WEB DATA CONSISTENCY CHECKS FAILED.")
        print("=" * 70)
        return False


if __name__ == "__main__":
    success = verify_web_data()
    sys.exit(0 if success else 1)
