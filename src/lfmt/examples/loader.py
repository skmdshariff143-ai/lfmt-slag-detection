"""
Data and metadata loader for verified examples.
"""

from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional, Union
import numpy as np

from lfmt.examples.integrity import verify_example_integrity


@dataclass
class LoadedExample:
    """Container for loaded example data and metadata."""
    example_id: str
    title: str
    category: str
    source_type: str
    data: Union[np.ndarray, Path]
    time_vector: Optional[np.ndarray]
    metadata: Dict[str, Any]
    ground_truth: Optional[Dict[str, Any]]
    expected_result: Dict[str, Any]
    is_installed: bool


def load_example(example_id: str, base_dir: Optional[Path] = None) -> LoadedExample:
    """
    Load a verified example by ID.
    Performs integrity check before loading numerical arrays.
    """
    if base_dir is None:
        # Default repo data/examples path
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        base_dir = repo_root / "data" / "examples"

    ex_dir = base_dir / example_id
    if not ex_dir.exists():
        raise FileNotFoundError(f"Example '{example_id}' not found in {base_dir}")

    # Integrity verification
    is_valid, errors = verify_example_integrity(ex_dir)
    if not is_valid:
        raise ValueError(f"Integrity check failed for example '{example_id}': {'; '.join(errors)}")

    # Load metadata
    meta_p = ex_dir / "metadata.json"
    if not meta_p.exists():
        raise FileNotFoundError(f"Metadata missing for example '{example_id}'")
    metadata = json.loads(meta_p.read_text(encoding="utf-8"))

    # Load expected result
    exp_p = ex_dir / "expected_result.json"
    expected_result = json.loads(exp_p.read_text(encoding="utf-8")) if exp_p.exists() else {}

    # Load ground truth if present (for evaluation only)
    gt_p = ex_dir / "ground_truth.json"
    ground_truth = json.loads(gt_p.read_text(encoding="utf-8")) if gt_p.exists() else None

    # Load data array
    data: Union[np.ndarray, Path]
    t_vec: Optional[np.ndarray] = None
    is_installed = True

    npz_p = ex_dir / "thermograms.npz"
    npy_p = ex_dir / "thermal_frame.npy"

    if npz_p.exists():
        loaded = np.load(npz_p)
        data = loaded["surface_temperature"]
        if "time_vector" in loaded:
            t_vec = loaded["time_vector"]
    elif npy_p.exists():
        data = np.load(npy_p)
    elif metadata.get("source_type") == "EXTERNAL_MEASURED":
        # External dataset
        src_p = ex_dir / "source.json"
        src_info = json.loads(src_p.read_text(encoding="utf-8")) if src_p.exists() else {}
        raw_rel = src_info.get("local_raw_path", "")
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        raw_abs = repo_root / raw_rel
        if raw_abs.exists():
            data = raw_abs
            is_installed = True
        else:
            data = raw_abs
            is_installed = False
    else:
        raise FileNotFoundError(f"No valid data file (thermograms.npz or thermal_frame.npy) in {ex_dir}")

    return LoadedExample(
        example_id=example_id,
        title=metadata.get("title", example_id),
        category=metadata.get("category", "UNKNOWN"),
        source_type=metadata.get("source_type", "UNKNOWN"),
        data=data,
        time_vector=t_vec,
        metadata=metadata,
        ground_truth=ground_truth,
        expected_result=expected_result,
        is_installed=is_installed
    )
