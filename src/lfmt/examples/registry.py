# Master Example Registry
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from lfmt.examples.loader import load_example, LoadedExample
from lfmt.examples.integrity import verify_example_integrity


class ExampleRegistry:
    """Scientific Example Data Registry."""

    _default_instance: Optional[ExampleRegistry] = None

    def __init__(self, examples_dir: Optional[Path] = None):
        if examples_dir is None:
            repo_root = Path(__file__).resolve().parent.parent.parent.parent
            examples_dir = repo_root / "data" / "examples"
        self.examples_dir = Path(examples_dir)

    @classmethod
    def get_default(cls) -> ExampleRegistry:
        if cls._default_instance is None:
            cls._default_instance = cls()
        return cls._default_instance

    def list_examples(self) -> List[Dict[str, Any]]:
        manifest_p = self.examples_dir / "examples_manifest.json"
        if not manifest_p.exists():
            # If manifest doesn't exist in custom dir, scan subdirectories
            found = []
            for sub in sorted(self.examples_dir.iterdir()):
                if sub.is_dir():
                    meta_p = sub / "metadata.json"
                    if meta_p.exists():
                        try:
                            meta = json.loads(meta_p.read_text(encoding="utf-8"))
                            found.append({
                                "id": sub.name,
                                "title": meta.get("title", sub.name),
                                "category": meta.get("category", "A"),
                                "source_type": meta.get("source_type", "NUMERICAL_FEM"),
                                "material": meta.get("material", "mild_steel"),
                                "excitation_type": meta.get("excitation", {}).get("type", "lfmt_chirp"),
                                "defect_description": meta.get("defects", [{}])[0].get("defect_type", "None") if meta.get("defects") else "None",
                                "frames": meta.get("time", {}).get("n_frames", 101),
                                "resolution": meta.get("camera", {}).get("resolution", [28, 40]),
                                "frame_rate_hz": meta.get("camera", {}).get("frame_rate_hz", 10.0),
                                "duration_s": meta.get("time", {}).get("duration_s", 10.0),
                                "temperature_unit_status": meta.get("temperature_unit_status", "SOURCE_VERIFIED"),
                                "radiometric_status": meta.get("radiometric_status", "VERIFIED_NUMERICAL"),
                                "fov_status": "VERIFIED_100x70_MM",
                                "GT_available": (sub / "ground_truth.json").exists(),
                                "example_available": (sub / "thermograms.npz").exists() or (sub / "thermal_frame.npy").exists(),
                                "supported_methods": ["raw_contrast", "lfmt_matched_filter", "pct", "spct", "rpt"]
                            })
                        except Exception:
                            pass
            return found

        manifest = json.loads(manifest_p.read_text(encoding="utf-8"))
        examples_list = manifest.get("examples", [])

        # Update dynamic installation state
        for ex in examples_list:
            ex_id = ex.get("id")
            ex_dir = self.examples_dir / ex_id
            if ex.get("source_type") == "EXTERNAL_MEASURED":
                data_p = Path(__file__).resolve().parent.parent.parent.parent / ex.get("data_path", "")
                ex["example_available"] = data_p.exists()
            else:
                ex["example_available"] = (ex_dir / "thermograms.npz").exists() or (ex_dir / "thermal_frame.npy").exists()

        return examples_list

    def get_all_ids(self) -> List[str]:
        return [ex["id"] for ex in self.list_examples()]

    def get_example_metadata(self, example_id: str) -> Optional[Dict[str, Any]]:
        meta_p = self.examples_dir / example_id / "metadata.json"
        if not meta_p.exists():
            return None
        return json.loads(meta_p.read_text(encoding="utf-8"))

    def get_expected_result(self, example_id: str) -> Optional[Dict[str, Any]]:
        exp_p = self.examples_dir / example_id / "expected_result.json"
        if not exp_p.exists():
            return None
        return json.loads(exp_p.read_text(encoding="utf-8"))

    def get_ground_truth(self, example_id: str) -> Optional[Dict[str, Any]]:
        gt_p = self.examples_dir / example_id / "ground_truth.json"
        if not gt_p.exists():
            return None
        return json.loads(gt_p.read_text(encoding="utf-8"))

    def verify_example(self, example_id: str) -> Dict[str, Any]:
        ex_dir = self.examples_dir / example_id
        if not ex_dir.exists():
            return {
                "status": "FAILED",
                "is_valid": False,
                "errors": [f"Example directory {example_id} does not exist"],
                "verified_files": [],
                "failed_files": [f"Example directory {example_id} does not exist"]
            }

        is_valid, errors = verify_example_integrity(ex_dir)
        verified_files = []
        sha_p = ex_dir / "sha256.txt"
        if sha_p.exists():
            for line in sha_p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split(maxsplit=1)
                    if len(parts) == 2:
                        verified_files.append(parts[1])

        return {
            "status": "VERIFIED" if is_valid else "FAILED",
            "is_valid": is_valid,
            "errors": errors,
            "verified_files": verified_files,
            "failed_files": errors
        }

    def load(self, example_id: str) -> LoadedExample:
        return load_example(example_id, base_dir=self.examples_dir)


# Module-level convenience functions mirroring the singleton
def list_examples() -> List[Dict[str, Any]]:
    return ExampleRegistry.get_default().list_examples()

def get_example_metadata(example_id: str) -> Optional[Dict[str, Any]]:
    return ExampleRegistry.get_default().get_example_metadata(example_id)

def get_expected_result(example_id: str) -> Optional[Dict[str, Any]]:
    return ExampleRegistry.get_default().get_expected_result(example_id)

def get_ground_truth(example_id: str) -> Optional[Dict[str, Any]]:
    return ExampleRegistry.get_default().get_ground_truth(example_id)

def verify_example(example_id: str) -> Dict[str, Any]:
    return ExampleRegistry.get_default().verify_example(example_id)

def load(example_id: str) -> LoadedExample:
    return ExampleRegistry.get_default().load(example_id)
