"""
Unit and integrity tests for the verified reference example data library.
"""

import json
from pathlib import Path
import numpy as np
import pytest

from src.lfmt.examples.registry import ExampleRegistry
from src.lfmt.examples.integrity import verify_example_integrity, compute_sha256


def test_manifest_schema_and_entries():
    manifest_path = Path("data/examples/examples_manifest.json")
    assert manifest_path.is_file(), "examples_manifest.json must exist"
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    assert manifest.get("schema_version") == "3.0.0"
    assert "examples" in manifest
    assert len(manifest["examples"]) == 6
    
    expected_ids = {
        "healthy_lfmt",
        "slag_shallow",
        "slag_deep",
        "multi_slag",
        "single_thermal_frame",
        "measured_polyu_preview"
    }
    manifest_ids = {ex["id"] for ex in manifest["examples"]}
    assert manifest_ids == expected_ids


def test_registry_listing():
    examples = ExampleRegistry.list_examples()
    assert len(examples) == 6
    
    categories = {ex["category"] for ex in examples}
    assert "A" in categories
    assert "B" in categories


def test_all_examples_integrity():
    for ex_id in ExampleRegistry.get_all_ids():
        status = ExampleRegistry.verify_example(ex_id)
        assert status["status"] == "VERIFIED", f"Integrity check failed for {ex_id}: {status}"
        assert len(status["verified_files"]) > 0
        assert len(status["failed_files"]) == 0


def test_example_data_finite_and_physical():
    for ex_id in ["healthy_lfmt", "slag_shallow", "slag_deep", "multi_slag", "single_thermal_frame"]:
        loaded = ExampleRegistry.load(ex_id)
        assert loaded.is_installed is True
        arr = loaded.data
        assert arr is not None
        assert np.all(np.isfinite(arr)), f"Non-finite values found in {ex_id}"
        assert np.min(arr) > 270.0, f"Temperature under physical lower bound in {ex_id}: min={np.min(arr)}"
        assert np.max(arr) < 400.0, f"Temperature over physical upper bound in {ex_id}: max={np.max(arr)}"
        
        # Verify dimensions match metadata
        meta = loaded.metadata
        res = meta.get("spatial_resolution_px", [28, 40])
        if ex_id == "single_thermal_frame":
            assert arr.shape == tuple(res), f"Shape mismatch for {ex_id}: {arr.shape} vs {res}"
        else:
            n_frames = meta.get("n_frames", 101)
            assert arr.shape == (n_frames, res[0], res[1]), f"Shape mismatch for {ex_id}: {arr.shape}"


def test_ground_truth_isolation():
    for ex_id in ["slag_shallow", "slag_deep", "multi_slag"]:
        gt = ExampleRegistry.get_ground_truth(ex_id)
        assert gt is not None, f"Missing ground truth for {ex_id}"
        assert gt.get("evaluation_only") is True
        assert "defects" in gt
        assert len(gt["defects"]) >= 1
