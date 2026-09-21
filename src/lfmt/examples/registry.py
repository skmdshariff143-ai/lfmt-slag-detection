# Master Example Registry
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

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

    @classmethod
    def get_all_ids(cls) -> List[str]:
        return [ex["id"] for ex in cls.get_default().list_examples()]

    @classmethod
    def list_examples(cls) -> List[Dict[str, Any]]:
        inst = cls.get_default() if cls is ExampleRegistry else cls
        return inst._list_examples_impl()

    def _list_examples_impl(self) -> List[Dict[str, Any]]:
        manifest_p = self.examples_dir / "examples_manifest.json"
        if not manifest_p.exists():
            return []

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

    @classmethod
    def get_example_metadata(cls, example_id: str) -> Optional[Dict[str, Any]]:
        inst = cls.get_default() if isinstance(cls, type) else cls
        return inst._get_example_metadata_impl(example_id)

    def _get_example_metadata_impl(self, example_id: str) -> Optional[Dict[str, Any]]:
        meta_p = self.examples_dir / example_id / "metadata.json"
        if not meta_p.exists():
            return None
        return json.loads(meta_p.read_text(encoding="utf-8"))

    @classmethod
    def get_expected_result(cls, example_id: str) -> Optional[Dict[str, Any]]:
        inst = cls.get_default() if isinstance(cls, type) else cls
        return inst._get_expected_result_impl(example_id)

    def _get_expected_result_impl(self, example_id: str) -> Optional[Dict[str, Any]]:
        exp_p = self.examples_dir / example_id / "expected_result.json"
        if not exp_p.exists():
            return None
        return json.loads(exp_p.read_text(encoding="utf-8"))

    @classmethod
    def get_ground_truth(cls, example_id: str) -> Optional[Dict[str, Any]]:
        inst = cls.get_default() if isinstance(cls, type) else cls
        return inst._get_ground_truth_impl(example_id)

    def _get_ground_truth_impl(self, example_id: str) -> Optional[Dict[str, Any]]:
        gt_p = self.examples_dir / example_id / "ground_truth.json"
        if not gt_p.exists():
            return None
        return json.loads(gt_p.read_text(encoding="utf-8"))

    @classmethod
    def verify_example(cls, example_id: str) -> Dict[str, Any]:
        inst = cls.get_default() if isinstance(cls, type) else cls
        return inst._verify_example_impl(example_id)

    def _verify_example_impl(self, example_id: str) -> Dict[str, Any]:
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

    @classmethod
    def load(cls, example_id: str) -> LoadedExample:
        inst = cls.get_default() if isinstance(cls, type) else cls
        return inst._load_impl(example_id)

    def _load_impl(self, example_id: str) -> LoadedExample:
        return load_example(example_id, base_dir=self.examples_dir)
