"""
Scientific Non-Leakage Test:
Guarantees that ground_truth.json is strictly isolated and has ZERO influence
on the inference outputs, preprocessing, feature extraction, or consensus verdict.
"""

import json
import shutil
import tempfile
from pathlib import Path

from lfmt.examples.registry import ExampleRegistry
from lfmt.analysis.analyzer import AutoDefectAnalyzer


def test_no_gt_leakage_on_shallow_slag():
    """
    Test that altering ground_truth.json does not affect inference outputs.
    """
    analyzer = AutoDefectAnalyzer()
    registry_orig = ExampleRegistry()
    loaded_original = registry_orig.load("slag_shallow")
    
    # 1. Base inference with original ground truth
    res_orig = analyzer.analyze(
        source=loaded_original.data,
        metadata_override=loaded_original.metadata,
        apply_baseline=True,
        smooth_sigma_px=0.0
    )
    dict_orig = res_orig.to_dict()
    
    # 2. Mutate ground truth in temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_ex_dir = Path(tmpdir) / "slag_shallow"
        shutil.copytree("data/examples/slag_shallow", tmp_ex_dir)
        
        # Heavily alter ground truth values
        gt_path = tmp_ex_dir / "ground_truth.json"
        assert gt_path.exists()
        
        mutated_gt = {
            "evaluation_only": True,
            "defects": [
                {
                    "defect_id": "MUTATED_BOGUS_DEFECT",
                    "defect_type": "DELAMINATION_VOID",
                    "diameter_mm": 25.0,
                    "depth_mm": 4.5,
                    "thickness_mm": 2.0,
                    "center_x_mm": 5.0,
                    "center_y_mm": 5.0
                }
            ]
        }
        gt_path.write_text(json.dumps(mutated_gt, indent=2), encoding="utf-8")
        
        # Recompute sha256 so load succeeds in temp directory with mutated GT
        lines = []
        import hashlib
        for p in sorted(tmp_ex_dir.iterdir()):
            if p.is_file() and p.name != "sha256.txt":
                h = hashlib.sha256()
                with open(p, "rb") as f:
                    while chunk := f.read(65536):
                        h.update(chunk)
                lines.append(f"{h.hexdigest()}  {p.name}")
        (tmp_ex_dir / "sha256.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        
        # Load from mutated temporary registry
        temp_registry = ExampleRegistry(examples_dir=Path(tmpdir))
        loaded_mutated = temp_registry.load("slag_shallow")
        
        # Run inference on mutated example
        res_mutated = analyzer.analyze(
            source=loaded_mutated.data,
            metadata_override=loaded_mutated.metadata,
            apply_baseline=True,
            smooth_sigma_px=0.0
        )
        dict_mutated = res_mutated.to_dict()
    
    # 3. Assert exact numerical and structural equality between orig and mutated
    assert dict_orig["consensus_verdict"]["is_anomaly_detected"] == dict_mutated["consensus_verdict"]["is_anomaly_detected"]
    assert dict_orig["consensus_verdict"]["likely_defect_type"] == dict_mutated["consensus_verdict"]["likely_defect_type"]
    assert dict_orig["consensus_verdict"]["consensus_confidence"] == dict_mutated["consensus_verdict"]["consensus_confidence"]
    assert dict_orig["consensus_verdict"]["method_agreement_ratio"] == dict_mutated["consensus_verdict"]["method_agreement_ratio"]
    
    # Defects candidate count and geometry must be completely unperturbed by GT mutation
    assert len(dict_orig["defects"]) == len(dict_mutated["defects"])
    if dict_orig["defects"]:
        d0_orig = dict_orig["defects"][0]
        d0_mut = dict_mutated["defects"][0]
        assert d0_orig["centroid_px"] == d0_mut["centroid_px"]
        assert d0_orig["centroid_mm"] == d0_mut["centroid_mm"]
        assert d0_orig["equivalent_diameter_mm"] == d0_mut["equivalent_diameter_mm"]
        assert d0_orig["area_px"] == d0_mut["area_px"]
        assert d0_orig["confidence_score"] == d0_mut["confidence_score"]
