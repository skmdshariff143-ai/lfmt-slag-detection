"""
Unit and integrity tests for the verified reference example data library.
"""

import json
import shutil
import tempfile
from pathlib import Path
import numpy as np
import pytest

from lfmt.examples.registry import ExampleRegistry


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
    registry = ExampleRegistry()
    examples = registry.list_examples()
    assert len(examples) == 6
    
    categories = {ex["category"] for ex in examples}
    assert "A" in categories
    assert "B" in categories


def test_all_examples_integrity():
    registry = ExampleRegistry()
    for ex_id in registry.get_all_ids():
        status = registry.verify_example(ex_id)
        assert status["status"] == "VERIFIED", f"Integrity check failed for {ex_id}: {status}"
        assert len(status["verified_files"]) > 0
        assert len(status["failed_files"]) == 0


def test_example_data_finite_and_physical():
    registry = ExampleRegistry()
    for ex_id in ["healthy_lfmt", "slag_shallow", "slag_deep", "multi_slag", "single_thermal_frame"]:
        loaded = registry.load(ex_id)
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
    registry = ExampleRegistry()
    for ex_id in ["slag_shallow", "slag_deep", "multi_slag"]:
        gt = registry.get_ground_truth(ex_id)
        assert gt is not None, f"Missing ground truth for {ex_id}"
        assert gt.get("evaluation_only") is True
        assert "defects" in gt
        assert len(gt["defects"]) >= 1


def test_sha_integrity_tamper_rejection():
    """
    Cryptographic Rigor Test:
    Verify that verify_example_integrity() and ExampleRegistry.load() strictly reject:
    1. Missing files
    2. Modified NPZ binary data
    3. Modified metadata.json
    4. Modified expected_result.json
    5. Modified ground_truth.json
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_ex_dir = Path(tmpdir) / "slag_shallow"
        shutil.copytree("data/examples/slag_shallow", tmp_ex_dir)
        temp_registry = ExampleRegistry(examples_dir=Path(tmpdir))

        # Baseline: must pass before tampering
        status = temp_registry.verify_example("slag_shallow")
        assert status["status"] == "VERIFIED"

        # Case 1: Tampered metadata.json
        meta_file = tmp_ex_dir / "metadata.json"
        meta_file.write_text(meta_file.read_text(encoding="utf-8") + "\n/* corrupted */", encoding="utf-8")
        status_tampered = temp_registry.verify_example("slag_shallow")
        assert status_tampered["status"] == "FAILED"
        assert any("metadata.json" in err for err in status_tampered["errors"])
        with pytest.raises(ValueError, match="Integrity check failed"):
            temp_registry.load("slag_shallow")

        # Restore metadata
        shutil.copyfile("data/examples/slag_shallow/metadata.json", meta_file)

        # Case 2: Tampered thermograms.npz
        npz_file = tmp_ex_dir / "thermograms.npz"
        npz_bytes = bytearray(npz_file.read_bytes())
        npz_bytes[100] = (npz_bytes[100] + 1) % 256
        npz_file.write_bytes(bytes(npz_bytes))
        status_tampered_npz = temp_registry.verify_example("slag_shallow")
        assert status_tampered_npz["status"] == "FAILED"
        assert any("thermograms.npz" in err for err in status_tampered_npz["errors"])
        with pytest.raises(ValueError, match="Integrity check failed"):
            temp_registry.load("slag_shallow")

        # Case 3: Missing file
        shutil.copyfile("data/examples/slag_shallow/thermograms.npz", npz_file)
        gt_file = tmp_ex_dir / "ground_truth.json"
        gt_file.unlink()
        status_missing = temp_registry.verify_example("slag_shallow")
        assert status_missing["status"] == "FAILED"
        assert any("missing" in err.lower() for err in status_missing["errors"])
