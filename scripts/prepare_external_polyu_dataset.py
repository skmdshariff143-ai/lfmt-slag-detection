#!/usr/bin/env python3
"""
Dataset Preparation and Validation Script for External Measured Thermography.

Dataset: PolyU Mild Steel Pulsed Thermography (DOI: 10.60933/PRDR/HJYNZB)
Specimen: Mild steel plate (150 x 150 x 10 mm) with manufactured circular flat-bottom holes
Excitation: Pulsed optical flash (6 kJ, 4 ms)
Camera: FLIR A655sc (640x480 LWIR @ 50 Hz)

Note: External measured transfer example only. Not physical LFMT slag validation.
"""

from __future__ import annotations
import json
import os
import sys
import hashlib
from pathlib import Path
import numpy as np

# Ensure repository root is on sys.path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

from lfmt.io_experimental import ExperimentalDataLoader, ExperimentalSequence


def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def main():
    raw_dir = repo_root / "data" / "real_world_external" / "polyu_mild_steel_pulsed" / "raw"
    results_dir = repo_root / "results" / "external_real_world" / "polyu_mild_steel_pulsed"
    val_dir = results_dir / "validation"
    val_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = raw_dir / "MS-facq-50Hz-air-cir-1_0-999.zip"
    if not zip_path.exists():
        print(f"Error: Archive not found at {zip_path}")
        sys.exit(1)

    print("==================================================================")
    print("PREPARING & VALIDATING EXTERNAL MEASURED THERMOGRAPHY DATASET")
    print(f"Archive: {zip_path.name}")
    print("==================================================================")

    # 1. File hash verification
    print("1. Verifying SHA-256 archive checksum...")
    sha256 = compute_sha256(zip_path)
    file_size = zip_path.stat().st_size
    print(f"   Size: {file_size:,} bytes")
    print(f"   SHA-256: {sha256}")

    # 2. Ingestion via ExperimentalDataLoader
    # We load with temporal subsampling = 2 for balanced memory/speed (500 frames @ 25 Hz effective = 20 s total)
    print("\n2. Ingesting frame sequence from CSV archive...")
    seq = ExperimentalDataLoader.load_csv_zip_archive(
        zip_path=zip_path,
        frame_rate_hz=50.0,
        fov_mm=(150.0, 150.0),
        temp_units="C",
        subsample_step=2  # 500 frames across 20s (25 Hz)
    )

    # 3. Validation
    print("\n3. Validating physical sequence bounds and integrity...")
    val_results = ExperimentalDataLoader.validate_sequence(seq)
    val_results["archive_sha256"] = sha256
    val_results["archive_size_bytes"] = file_size
    val_results["dataset_doi"] = "10.60933/PRDR/HJYNZB"
    val_results["specimen_material"] = "Mild steel plate"
    val_results["specimen_dimensions_mm"] = [150.0, 150.0, 10.0]
    val_results["excitation_method"] = "pulsed_optical_flash"
    val_results["camera_model"] = "FLIR A655sc (640x480)"

    print("   Validation Result:")
    for k, v in val_results.items():
        print(f"     {k}: {v}")

    # Save validation report
    val_report_path = val_dir / "data_validation.json"
    with open(val_report_path, "w", encoding="utf-8") as f:
        json.dump(val_results, f, indent=2)
    print(f"\nSaved validation report to: {val_report_path}")

    # Save sequence summary
    summary_path = results_dir / "sequence_summary.json"
    summary_data = {
        "dataset_name": "PolyU Mild Steel Pulsed Thermography Transfer Example",
        "doi": "10.60933/PRDR/HJYNZB",
        "archive_file": zip_path.name,
        "archive_sha256": sha256,
        "archive_size_bytes": file_size,
        "specimen": {
            "material": "Mild steel",
            "geometry_mm": [150.0, 150.0, 10.0],
            "defects": "11 circular flat-bottom holes (diameters 2-10 mm, depths 0.5-5.0 mm)"
        },
        "acquisition": {
            "source_frame_rate_hz": 50.0,
            "effective_frame_rate_hz": seq.frame_rate_hz,
            "total_frames_processed": int(seq.surface_temperature.shape[0]),
            "spatial_resolution_px": [int(seq.surface_temperature.shape[1]), int(seq.surface_temperature.shape[2])],
            "total_duration_s": float(seq.time_vector[-1] - seq.time_vector[0]),
            "raw_temperature_units": seq.metadata.get("raw_units", "C"),
            "converted_temperature_units": seq.metadata.get("converted_units", "K"),
            "conversion_formula": seq.metadata.get("conversion_method", "")
        },
        "temperature_stats_kelvin": {
            "min": round(float(np.min(seq.surface_temperature)), 3),
            "max": round(float(np.max(seq.surface_temperature)), 3),
            "mean": round(float(np.mean(seq.surface_temperature)), 3),
            "ambient_baseline": round(float(np.mean(seq.surface_temperature[0])), 3),
            "peak_flash_temperature": round(float(np.max(seq.surface_temperature)), 3)
        }
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    print(f"Saved sequence summary to: {summary_path}")
    print("\nDataset preparation & validation completed successfully.")


if __name__ == "__main__":
    main()
